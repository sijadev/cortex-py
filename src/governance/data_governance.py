"""
Cortex Data Governance Engine
Verhindert unkontrollierte Dateneingabe in Neo4j mit intelligenter Template-Erkennung
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import os
import json

# Neo4j Integration - kann durch Umgebungsvariable deaktiviert werden
NEO4J_DISABLED = os.environ.get("NEO4J_DISABLED", "").lower() in ("1", "true", "yes")

try:
    if NEO4J_DISABLED:
        raise ImportError("Neo4j intentionally disabled")
    from neo4j import GraphDatabase

    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False


class ValidationLevel(Enum):
    STRICT = "strict"  # Blockiert bei Fehlern
    WARNING = "warning"  # Warnt, aber erlaubt
    LENIENT = "lenient"  # Nur Logging


@dataclass
class ValidationResult:
    passed: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


class Neo4jTemplateManager:
    """Verwaltet Templates in Neo4j als primäre Datenquelle"""

    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="neo4jtest"):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        # Verbindung erst bei Bedarf herstellen, nicht beim Import
        # self._connect()

    def _connect(self):
        """Verbindet zu Neo4j"""
        if not NEO4J_AVAILABLE:
            return False

        try:
            from neo4j.exceptions import ServiceUnavailable

            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Verwende einen sehr kurzen Timeout für die Connectivity-Prüfung
            self.driver.verify_connectivity()
            return True
        except (Exception, ServiceUnavailable):
            self.driver = None
            return False

    def is_connected(self):
        """Prüft Neo4j Verbindung"""
        # Lazy connection - verbinde erst wenn geprüft wird
        if self.driver is None and NEO4J_AVAILABLE:
            self._connect()
        return self.driver is not None

    def get_templates_for_project(self, project_type: str, keywords: List[str] = None) -> Dict:
        """Holt passende Templates aus Neo4j basierend auf Projekt-Typ und Keywords"""
        if not self.is_connected():
            return {}

        templates = {}
        keywords = keywords or []

        try:
            with self.driver.session() as session:
                # Korrigierte Cypher-Query ohne ORDER BY auf aggregierte Felder
                query = """
                MATCH (t:Template)
                WHERE t.project_types IS NULL OR $project_type IN t.project_types
                OPTIONAL MATCH (t)-[:CONTAINS_KEYWORD]->(k:Keyword)
                WHERE k.name IN $keywords
                WITH t, count(k) as keyword_matches
                RETURN t.name as name, t.required_sections as sections,
                       t.suggested_tags as tags, t.workflow_step as workflow_step,
                       t.content_standards as standards_json, t.usage_count as usage_count,
                       keyword_matches
                ORDER BY keyword_matches DESC, coalesce(usage_count, 0) DESC
                """

                result = session.run(query, project_type=project_type, keywords=keywords)

                for record in result:
                    template_name = record["name"]
                    standards = {}
                    if record["standards_json"]:
                        try:
                            standards = json.loads(record["standards_json"])
                        except:
                            standards = {}

                    templates[template_name] = {
                        "required_sections": record["sections"] or [],
                        "suggested_tags": record["tags"] or [],
                        "workflow_step": record["workflow_step"],
                        "content_standards": standards,
                        "relevance_score": record["keyword_matches"],
                    }
        except Exception as e:
            # Graceful error handling - return empty dict on any Neo4j errors
            return {}

        return templates

    def create_template_if_missing(
        self, project_type: str, project_name: str, keywords: List[str] = None
    ) -> Dict:
        """Erstellt automatisch ein Template falls keines existiert"""
        if not self.is_connected():
            return {}

        try:
            # Prüfe ob bereits Templates existieren
            existing = self.get_templates_for_project(project_type, keywords)
            if existing:
                return existing

            # Template-Namen erzeugen
            template_name = f"{project_type}_{project_name.lower().replace(' ', '_')}"

            # Basis-Template basierend auf Projekt-Typ erstellen
            template_config = self._generate_template_config(project_type, keywords or [])

            # In Neo4j speichern
            with self.driver.session() as session:
                session.run(
                    """
                    MERGE (t:Template {name: $name})
                    SET t.required_sections = $sections,
                        t.suggested_tags = $tags,
                        t.workflow_step = $workflow_step,
                        t.content_standards = $standards,
                        t.project_types = [$project_type],
                        t.created_at = datetime(),
                        t.auto_generated = true,
                        t.usage_count = 0
                """,
                    name=template_name,
                    sections=template_config["required_sections"],
                    tags=template_config["suggested_tags"],
                    workflow_step=template_config["workflow_step"],
                    standards=json.dumps(template_config["content_standards"]),
                    project_type=project_type,
                )

                # Keywords verknüpfen
                for keyword in keywords or []:
                    session.run(
                        """
                        MERGE (k:Keyword {name: $keyword})
                        MERGE (t:Template {name: $template_name})
                        MERGE (t)-[:CONTAINS_KEYWORD]->(k)
                    """,
                        keyword=keyword,
                        template_name=template_name,
                    )

            return {template_name: template_config}
        except Exception as e:
            # Graceful error handling - return empty dict on any Neo4j errors
            return {}

    def _generate_template_config(self, project_type: str, keywords: List[str]) -> Dict:
        """Generiert Template-Konfiguration basierend auf Projekt-Typ"""
        base_configs = {
            "research": {
                "required_sections": ["abstract", "methodology", "results", "conclusion"],
                "suggested_tags": ["research", "analysis", "findings"],
                "workflow_step": "research",
                "content_standards": {
                    "min_length": 1000,
                    "required_keywords": ["hypothesis", "data", "analysis"],
                },
            },
            "development": {
                "required_sections": ["overview", "requirements", "architecture", "implementation"],
                "suggested_tags": ["development", "technical", "implementation"],
                "workflow_step": "development",
                "content_standards": {
                    "min_length": 500,
                    "required_keywords": ["requirements", "architecture", "code"],
                },
            },
            "documentation": {
                "required_sections": ["purpose", "overview", "usage", "examples"],
                "suggested_tags": ["documentation", "guide", "reference"],
                "workflow_step": "documentation",
                "content_standards": {
                    "min_length": 300,
                    "required_keywords": ["usage", "example", "guide"],
                },
            },
            "meeting": {
                "required_sections": ["attendees", "agenda", "decisions", "action_items"],
                "suggested_tags": ["meeting", "decision", "action"],
                "workflow_step": "coordination",
                "content_standards": {
                    "min_length": 200,
                    "required_keywords": ["attendees", "decisions", "actions"],
                },
            },
        }

        # Standard-Template für unbekannte Typen
        default_config = {
            "required_sections": ["overview", "content", "summary"],
            "suggested_tags": ["general", project_type],
            "workflow_step": "general",
            "content_standards": {
                "min_length": 250,
                "required_keywords": keywords[:3] if keywords else [],
            },
        }

        config = base_configs.get(project_type.lower(), default_config)

        # Keywords integrieren
        if keywords:
            config["suggested_tags"].extend(keywords[:2])
            config["content_standards"]["required_keywords"].extend(keywords[:2])

        return config

    def update_template_usage(self, template_name: str):
        """Aktualisiert Nutzungsstatistiken für Template"""
        if not self.is_connected():
            return

        try:
            with self.driver.session() as session:
                session.run(
                    """
                    MATCH (t:Template {name: $name})
                    SET t.usage_count = coalesce(t.usage_count, 0) + 1,
                        t.last_used = datetime()
                """,
                    name=template_name,
                )
        except Exception as e:
            # Graceful handling - log but don't fail
            pass


class DataGovernanceEngine:
    def __init__(self, config_file: str = None):
        """Initialisiert die Data Governance Engine mit Neo4j als primäre Datenquelle."""

        # Standard-Konfiguration laden
        self.config = self._load_default_config()

        # Externe Konfiguration laden (falls vorhanden)
        if config_file and os.path.exists(config_file):
            self._load_external_config(config_file)

        # Neo4j Template Manager initialisieren
        self.neo4j_manager = Neo4jTemplateManager()

        # Driver für Kompatibilität - wird nicht mehr direkt verwendet
        self.driver = None

    def get_templates_for_context(
        self, project_type: str = None, project_name: str = None, keywords: List[str] = None
    ) -> Dict:
        """Intelligente Template-Auswahl basierend auf Kontext"""

        # Zuerst aus Neo4j versuchen
        if self.neo4j_manager.is_connected() and project_type:
            neo4j_templates = self.neo4j_manager.get_templates_for_project(project_type, keywords)

            # Wenn keine Templates gefunden, automatisch eines erstellen
            if not neo4j_templates and project_name:
                neo4j_templates = self.neo4j_manager.create_template_if_missing(
                    project_type, project_name, keywords
                )

            if neo4j_templates:
                return neo4j_templates

        # Fallback: Templates aus lokaler Konfiguration
        return self.get_templates()

    def validate_note_creation_with_context(
        self,
        name: str,
        content: str,
        description: str,
        note_type: str = "",
        project_type: str = None,
        project_name: str = None,
        keywords: List[str] = None,
    ) -> ValidationResult:
        """Erweiterte Validierung mit automatischer Template-Erkennung"""

        # Keywords aus Content extrahieren falls nicht gegeben
        if not keywords:
            keywords = self._extract_keywords_from_content(content)

        # Passende Templates holen
        context_templates = self.get_templates_for_context(project_type, project_name, keywords)

        # Bestes Template automatisch auswählen
        best_template = self._select_best_template(context_templates, keywords, content)

        # Template-Nutzung tracken
        if best_template and self.neo4j_manager.is_connected():
            self.neo4j_manager.update_template_usage(best_template)

        # Standard-Validierung mit ausgewähltem Template
        return self.validate_note_creation(name, content, description, note_type, best_template)

    def _extract_keywords_from_content(self, content: str) -> List[str]:
        """Extrahiert relevante Keywords aus Content"""
        # Einfache Keyword-Extraktion - kann mit NLP erweitert werden
        common_tech_keywords = [
            "python",
            "javascript",
            "react",
            "api",
            "database",
            "ml",
            "ai",
            "framework",
            "library",
            "development",
            "research",
            "analysis",
            "meeting",
            "project",
            "documentation",
            "guide",
            "tutorial",
        ]

        # Erweiterte Keywords für zusammengesetzte Begriffe
        compound_keywords = {
            "machine learning": ["ml", "machine", "learning"],
            "artificial intelligence": ["ai", "artificial", "intelligence"],
            "data science": ["data", "science"],
            "web development": ["web", "development"],
            "software engineering": ["software", "engineering"],
        }

        content_lower = content.lower()
        found_keywords = []

        # Prüfe erst einzelne Keywords - diese haben Priorität
        for keyword in common_tech_keywords:
            if keyword in content_lower:
                found_keywords.append(keyword)

        # Dann prüfe zusammengesetzte Begriffe - nur wenn noch Platz ist
        compound_found = []
        for compound, alternatives in compound_keywords.items():
            if compound in content_lower:
                compound_found.extend(alternatives)

        # Füge compound keywords hinzu, aber priorisiere die ursprünglichen
        all_keywords = found_keywords + compound_found

        # Duplikate entfernen und maximal 7 Keywords zurückgeben (erhöht von 5)
        unique_keywords = list(dict.fromkeys(all_keywords))  # Preserves order
        return unique_keywords[:7]

    def _select_best_template(self, templates: Dict, keywords: List[str], content: str) -> str:
        """Wählt das beste Template basierend auf Relevanz aus"""
        if not templates:
            return None

        # Wenn nur ein Template, das nehmen
        if len(templates) == 1:
            return list(templates.keys())[0]

        # Template mit höchster Relevanz
        best_template = None
        best_score = 0

        for template_name, template_config in templates.items():
            score = template_config.get("relevance_score", 0)

            # Zusätzliche Punkte für matching Keywords
            template_keywords = template_config.get("content_standards", {}).get(
                "required_keywords", []
            )
            keyword_matches = len(set(keywords) & set(template_keywords))
            score += keyword_matches * 2

            if score > best_score:
                best_score = score
                best_template = template_name

        return best_template

    def _load_default_config(self) -> dict:
        """Lädt Standard-Konfiguration als Fallback."""
        return {
            "workflows": {
                "Python Knowledge Base": {
                    "steps": [
                        "Grundlagen",
                        "Frameworks",
                        "Testing & Automation",
                        "Machine Learning",
                    ],
                    "templates": ["Python Framework", "Programmiersprache-Geschichte"],
                    "auto_assign": True,
                }
            },
            "templates": {
                "Python Framework": {
                    "required_sections": ["Hauptmerkmale", "Verwendung", "Status"],
                    "suggested_tags": ["framework", "python"],
                    "workflow_step": "Frameworks",
                    "content_standards": {
                        "min_length": 150,
                        "required_keywords": ["python"],
                        "optional_keywords": ["framework", "web"],
                    },
                },
                "Programmiersprache-Geschichte": {
                    "required_sections": ["Entstehung", "Entwicklung"],
                    "suggested_tags": ["geschichte", "python"],
                    "workflow_step": "Grundlagen",
                    "content_standards": {
                        "min_length": 200,
                        "required_keywords": ["entwicklung"],
                        "optional_keywords": ["geschichte", "python"],
                    },
                },
            },
            "validation_rules": {
                "name_min_length": 3,
                "content_min_length": 20,
                "description_min_length": 10,
                "duplicate_threshold": 0.7,
                "auto_suggest_templates": True,
                "auto_suggest_workflow_steps": True,
                "auto_suggest_tags": True,
                "validation_level": "warning",  # STRICT, WARNING, or LENIENT
            },
        }

    def _load_external_config(self, config_file: str):
        """Lädt externe Konfiguration und merged sie mit Standard-Config."""
        try:
            import json
            import yaml

            with open(config_file, "r", encoding="utf-8") as f:
                if config_file.endswith(".json"):
                    external_config = json.load(f)
                elif config_file.endswith(".yaml") or config_file.endswith(".yml"):
                    external_config = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported config format: {config_file}")

            # Deep merge der Konfigurationen
            self.config = self._deep_merge(self.config, external_config)

        except Exception as e:
            print(f"⚠️ Fehler beim Laden der externen Konfiguration: {e}")
            print("📋 Verwende Standard-Konfiguration")

    def _deep_merge(self, base: dict, update: dict) -> dict:
        """Führt Deep-Merge zweier Dictionaries durch."""
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def set_neo4j_driver(self, driver):
        """Setzt Neo4j-Driver für dynamische Abfragen."""
        self.driver = driver

    def get_workflows(self) -> dict:
        """Gibt alle konfigurierten Workflows zurück."""
        if self.driver:
            # Dynamisch aus Neo4j laden
            return self._load_workflows_from_neo4j()
        return self.config.get("workflows", {})

    def get_templates(self) -> dict:
        """Gibt alle konfigurierten Templates zurück."""
        if self.driver:
            # Dynamisch aus Neo4j laden
            return self._load_templates_from_neo4j()
        return self.config.get("templates", {})

    def add_workflow(
        self, name: str, steps: List[str], templates: List[str] = None, auto_assign: bool = True
    ):
        """Fügt dynamisch einen neuen Workflow hinzu."""
        self.config["workflows"][name] = {
            "steps": steps,
            "templates": templates or [],
            "auto_assign": auto_assign,
        }

        if self.driver:
            self._save_workflow_to_neo4j(name, steps, templates, auto_assign)

    def add_template(
        self,
        name: str,
        required_sections: List[str],
        suggested_tags: List[str] = None,
        workflow_step: str = None,
        content_standards: dict = None,
    ):
        """Fügt dynamisch ein neues Template hinzu."""
        self.config["templates"][name] = {
            "required_sections": required_sections,
            "suggested_tags": suggested_tags or [],
            "workflow_step": workflow_step,
            "content_standards": content_standards or {"min_length": 100},
        }

        if self.driver:
            self._save_template_to_neo4j(
                name, required_sections, suggested_tags, workflow_step, content_standards
            )

    def update_validation_rules(self, rules: dict):
        """Aktualisiert Validierungsregeln dynamisch."""
        current_rules = self.config.get("validation_rules", {})
        current_rules.update(rules)
        self.config["validation_rules"] = current_rules

    def _load_workflows_from_neo4j(self) -> dict:
        """Lädt Workflows dynamisch aus Neo4j."""
        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (w:Workflow)
                    OPTIONAL MATCH (w)-[:HAS_STEP]->(s:Step)
                    OPTIONAL MATCH (w)-[:USES_TEMPLATE]->(t:Template)
                    RETURN w.name as workflow_name,
                           w.auto_assign as auto_assign,
                           collect(DISTINCT {name: s.name, order: s.order}) as steps,
                           collect(DISTINCT t.name) as templates
                    ORDER BY w.name
                """
                )

                workflows = {}
                for record in result:
                    # Steps nach Order sortieren
                    steps_data = [s for s in record["steps"] if s["name"]]
                    steps_data.sort(key=lambda x: x.get("order", 0))
                    step_names = [s["name"] for s in steps_data]

                    workflows[record["workflow_name"]] = {
                        "steps": step_names,
                        "templates": [t for t in record["templates"] if t],
                        "auto_assign": record["auto_assign"] or True,
                    }
                return workflows
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Workflows aus Neo4j: {e}")
            return self.config.get("workflows", {})

    def _load_templates_from_neo4j(self) -> dict:
        """Lädt Templates dynamisch aus Neo4j."""
        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (t:Template)
                    RETURN t.name as template_name,
                           t.required_sections as required_sections,
                           t.suggested_tags as suggested_tags,
                           t.workflow_step as workflow_step,
                           t.content_standards as content_standards,
                           t.min_length as min_length,
                           t.required_keywords as required_keywords,
                           t.optional_keywords as optional_keywords
                """
                )

                templates = {}
                for record in result:
                    # Behandle verschiedene Neo4j-Datentypen
                    required_sections = record["required_sections"] or []
                    if isinstance(required_sections, str):
                        required_sections = [s.strip() for s in required_sections.split(",")]

                    suggested_tags = record["suggested_tags"] or []
                    if isinstance(suggested_tags, str):
                        suggested_tags = [s.strip() for s in suggested_tags.split(",")]

                    required_keywords = record["required_keywords"] or []
                    if isinstance(required_keywords, str):
                        required_keywords = [s.strip() for s in required_keywords.split(",")]

                    optional_keywords = record["optional_keywords"] or []
                    if isinstance(optional_keywords, str):
                        optional_keywords = [s.strip() for s in optional_keywords.split(",")]

                    templates[record["template_name"]] = {
                        "required_sections": required_sections,
                        "suggested_tags": suggested_tags,
                        "workflow_step": record["workflow_step"],
                        "content_standards": {
                            "min_length": record["min_length"]
                            or record.get("content_standards", {}).get("min_length", 100),
                            "required_keywords": required_keywords,
                            "optional_keywords": optional_keywords,
                        },
                    }
                return templates
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Templates aus Neo4j: {e}")
            return self.config.get("templates", {})

    def _save_workflow_to_neo4j(
        self, name: str, steps: List[str], templates: List[str], auto_assign: bool
    ):
        """Speichert Workflow in Neo4j."""
        try:
            with self.driver.session() as session:
                # Workflow erstellen
                session.run(
                    """
                    MERGE (w:Workflow {name: $name})
                    SET w.auto_assign = $auto_assign
                """,
                    name=name,
                    auto_assign=auto_assign,
                )

                # Steps hinzufügen
                for i, step in enumerate(steps):
                    session.run(
                        """
                        MERGE (s:Step {name: $step})
                        SET s.order = $order
                        WITH s
                        MATCH (w:Workflow {name: $workflow})
                        MERGE (w)-[:HAS_STEP]->(s)
                    """,
                        step=step,
                        order=i + 1,
                        workflow=name,
                    )

                # Templates verknüpfen
                for template in templates or []:
                    session.run(
                        """
                        MATCH (w:Workflow {name: $workflow}), (t:Template {name: $template})
                        MERGE (w)-[:USES_TEMPLATE]->(t)
                    """,
                        workflow=name,
                        template=template,
                    )

        except Exception as e:
            print(f"⚠️ Fehler beim Speichern des Workflows in Neo4j: {e}")

    def _save_template_to_neo4j(
        self,
        name: str,
        required_sections: List[str],
        suggested_tags: List[str],
        workflow_step: str,
        content_standards: dict,
    ):
        """Speichert Template in Neo4j."""
        try:
            with self.driver.session() as session:
                session.run(
                    """
                    MERGE (t:Template {name: $name})
                    SET t.required_sections = $required_sections,
                        t.suggested_tags = $suggested_tags,
                        t.workflow_step = $workflow_step,
                        t.min_length = $min_length,
                        t.required_keywords = $required_keywords,
                        t.optional_keywords = $optional_keywords,
                        t.updated_at = timestamp()
                """,
                    name=name,
                    required_sections=required_sections,
                    suggested_tags=suggested_tags,
                    workflow_step=workflow_step,
                    min_length=content_standards.get("min_length", 100),
                    required_keywords=content_standards.get("required_keywords", []),
                    optional_keywords=content_standards.get("optional_keywords", []),
                )
        except Exception as e:
            print(f"⚠️ Fehler beim Speichern des Templates in Neo4j: {e}")

    def validate_note_creation(
        self,
        name: str,
        content: str,
        description: str,
        note_type: str,
        template: str = None,
        workflow_step: str = None,
    ) -> ValidationResult:
        """Hauptvalidierung für Note-Erstellung mit flexibler Konfiguration."""

        result = ValidationResult(passed=True, errors=[], warnings=[], suggestions=[])

        # Validierungsregeln aus Konfiguration laden
        rules = self.config.get("validation_rules", {})

        # **WICHTIG: Validation Level aus Konfiguration lesen**
        validation_level_str = rules.get("validation_level", "warning")
        try:
            validation_level = ValidationLevel(validation_level_str.lower())
        except ValueError:
            validation_level = ValidationLevel.WARNING

        # 1. Basis-Validierungen mit konfigurierbaren Regeln
        self._validate_required_fields(result, name, content, description, rules, validation_level)
        self._validate_naming_conventions(result, name, validation_level)
        self._validate_content_quality(result, content, validation_level)

        # 2. Template-Validierung (dynamisch)
        templates = self.get_templates()
        if template and template in templates:
            self._validate_template_compliance(result, content, template, templates[template], validation_level)
        elif rules.get("auto_suggest_templates", True):
            suggested_template = self._suggest_template_dynamic(content, note_type, templates)
            if suggested_template:
                result.suggestions.append(f"Empfohlenes Template: {suggested_template}")

        # 3. Workflow-Integration (dynamisch)
        if not workflow_step and rules.get("auto_suggest_workflow_steps", True):
            workflows = self.get_workflows()
            suggested_step = self._suggest_workflow_step_dynamic(content, note_type, workflows)
            if suggested_step:
                result.suggestions.append(f"Empfohlener Workflow-Step: {suggested_step}")

        # 4. Tag-Suggestions (enhanced with performance tags)
        if rules.get("auto_suggest_tags", True):
            # Use the enhanced _suggest_tags method that includes performance tags
            suggested_tags = self._suggest_tags(content, note_type, template)

            # Also add dynamic template-based tags
            dynamic_tags = self._suggest_tags_dynamic(content, note_type, template, templates)

            # Combine all tags, removing duplicates
            if suggested_tags or dynamic_tags:
                all_tags = list(set(suggested_tags + dynamic_tags))
                if all_tags:
                    result.suggestions.append(f"Empfohlene Tags: {', '.join(all_tags)}")

        # 5. Duplikat-Warnung (konfigurierbar)
        if self._check_potential_duplicate_dynamic(name, rules.get("duplicate_threshold", 0.7)):
            duplicate_message = f"Ähnlicher Name bereits vorhanden"
            if validation_level == ValidationLevel.STRICT:
                result.errors.append(duplicate_message)
            else:
                result.warnings.append(duplicate_message)

        # **VALIDATION LEVEL ENFORCEMENT - Das war das fehlende Stück!**
        if validation_level == ValidationLevel.STRICT:
            # Im STRICT Modus: Alle Errors und kritische Warnings blockieren
            result.passed = len(result.errors) == 0
        elif validation_level == ValidationLevel.WARNING:
            # Im WARNING Modus: Nur schwere Errors blockieren
            critical_errors = [e for e in result.errors if "muss mindestens" in e or "darf nicht leer" in e]
            result.passed = len(critical_errors) == 0
        elif validation_level == ValidationLevel.LENIENT:
            # Im LENIENT Modus: Fast alles durchlassen, nur komplett ungültige Daten blockieren
            blocking_errors = [e for e in result.errors if "darf nicht leer" in e or "darf nicht None" in e]
            result.passed = len(blocking_errors) == 0

        return result

    def _validate_required_fields(
        self, result: ValidationResult, name: str, content: str, description: str, rules: dict, validation_level: ValidationLevel
    ):
        """Validiert Pflichtfelder mit Validation Level Enforcement."""
        # Name validation
        if not name or len(name.strip()) < rules.get("name_min_length", 3):
            message = f"Name muss mindestens {rules.get('name_min_length', 3)} Zeichen haben"
            if validation_level == ValidationLevel.STRICT:
                result.errors.append(message)
            elif validation_level == ValidationLevel.WARNING:
                result.warnings.append(message)
            # In LENIENT mode, only add as suggestion

        # Content validation
        if not content or len(content.strip()) < rules.get("content_min_length", 20):
            message = f"Content muss mindestens {rules.get('content_min_length', 20)} Zeichen haben"
            if validation_level == ValidationLevel.STRICT:
                result.errors.append(message)
            elif validation_level == ValidationLevel.WARNING:
                result.errors.append(message)  # Content length is critical even in WARNING mode
            else:  # LENIENT
                result.warnings.append(message)

        # Description validation
        if not description or len(description.strip()) < rules.get("description_min_length", 10):
            message = f"Beschreibung sollte mindestens {rules.get('description_min_length', 10)} Zeichen haben"
            if validation_level == ValidationLevel.STRICT:
                result.errors.append(message)
            else:
                result.warnings.append(message)

    def _validate_naming_conventions(self, result: ValidationResult, name: str, validation_level: ValidationLevel):
        """Validiert Namenskonventionen mit Validation Level Enforcement."""
        # Prüfe auf None oder leeren Namen
        if name is None or name == "":
            message = "Name darf nicht leer oder None sein"
            result.errors.append(message)  # This is always an error regardless of level
            return

        # Keine Sonderzeichen außer Leerzeichen, Bindestriche
        if not re.match(r"^[a-zA-Z0-9\s\-.]+$", name):
            message = "Name enthält ungültige Zeichen"
            result.errors.append(message)  # Always an error, regardless of validation level
            return

        # Keine generischen Namen
        generic_names = ["test", "note", "example", "temp", "new"]
        if name.lower().strip() in generic_names:
            message = f"Generischer Name '{name}' - bitte spezifischer"
            if validation_level == ValidationLevel.STRICT:
                result.errors.append(message)
            else:
                result.warnings.append(message)

    def _validate_content_quality(self, result: ValidationResult, content: str, validation_level: ValidationLevel):
        """Validiert Content-Qualität mit Validation Level Enforcement."""
        # Prüfe auf None oder leeren Content
        if content is None:
            result.errors.append("Content darf nicht None sein")  # Always an error
            return

        if len(content) < 100:
            message = "Content ist sehr kurz - mehr Details empfohlen"
            if validation_level == ValidationLevel.STRICT:
                result.warnings.append(message)
            elif validation_level == ValidationLevel.WARNING:
                result.suggestions.append(message)
            # In LENIENT mode, ignore this

        # Prüfe auf Markdown-Struktur
        if not any(marker in content for marker in ["#", "**", "*", "-", "1."]):
            message = "Strukturierung mit Markdown empfohlen"
            if validation_level == ValidationLevel.STRICT:
                result.warnings.append(message)
            else:
                result.suggestions.append(message)

        # Prüfe auf Code-Blöcke bei Code-Content
        if "def " in content or "class " in content or "import " in content:
            if "```" not in content:
                message = "Code sollte in Markdown-Code-Blöcken (```) stehen"
                if validation_level == ValidationLevel.STRICT:
                    result.warnings.append(message)
                else:
                    result.suggestions.append(message)

    def _validate_template_compliance(
        self, result: ValidationResult, content: str, template: str, template_rules: dict, validation_level: ValidationLevel
    ):
        """Validiert Template-Konformität mit Validation Level Enforcement."""
        templates = self.get_templates()
        if template in templates:
            # Prüfe required sections
            for section in template_rules["required_sections"]:
                if section.lower() not in content.lower():
                    message = f"Template-Sektion '{section}' fehlt"
                    if validation_level == ValidationLevel.STRICT:
                        result.errors.append(message)
                    else:
                        result.warnings.append(message)

            # Prüfe Content-Standards
            min_length = template_rules.get("content_standards", {}).get("min_length", 0)
            if len(content) < min_length:
                message = f"Content sollte mindestens {min_length} Zeichen lang sein"
                if validation_level == ValidationLevel.STRICT:
                    result.errors.append(message)
                else:
                    result.warnings.append(message)

            required_keywords = template_rules.get("content_standards", {}).get(
                "required_keywords", []
            )
            for keyword in required_keywords:
                if keyword.lower() not in content.lower():
                    message = f"Keyword '{keyword}' fehlt im Content"
                    if validation_level == ValidationLevel.STRICT:
                        result.errors.append(message)
                    elif validation_level == ValidationLevel.WARNING:
                        result.warnings.append(message)
                    # In LENIENT mode, ignore missing keywords

    def _suggest_template(self, content: str, note_type: str) -> Optional[str]:
        """Schlägt Template basierend auf Content vor."""
        content_lower = content.lower()

        if "framework" in content_lower and "python" in content_lower:
            return "Python Framework"
        elif "geschichte" in content_lower or "entwicklung" in content_lower:
            return "Programmiersprache-Geschichte"
        elif note_type == "framework":
            return "Python Framework"

        return None

    def _suggest_template_dynamic(
        self, content: str, note_type: str, templates: dict
    ) -> Optional[str]:
        """Schlägt Template basierend auf dynamischer Analyse vor."""
        # Prüfe auf None-Content
        if content is None:
            return None

        content_lower = content.lower()

        for template_name, rules in templates.items():
            required_keywords = rules.get("content_standards", {}).get("required_keywords", [])
            if all(kw in content_lower for kw in required_keywords):
                return template_name

        return None

    def _suggest_workflow_step(self, content: str, note_type: str) -> Optional[str]:
        """Schlägt Workflow-Step vor."""
        content_lower = content.lower()

        if any(word in content_lower for word in ["django", "flask", "fastapi"]):
            return "Frameworks"
        elif any(word in content_lower for word in ["pytest", "testing", "test"]):
            return "Testing & Automation"
        elif any(
            word in content_lower for word in ["tensorflow", "pytorch", "ml", "machine learning"]
        ):
            return "Machine Learning"
        elif any(word in content_lower for word in ["python", "guido", "geschichte"]):
            return "Grundlagen"

        return None

    def _suggest_workflow_step_dynamic(
        self, content: str, note_type: str, workflows: dict
    ) -> Optional[str]:
        """Schlägt Workflow-Step basierend auf dynamischer Analyse vor."""
        # Null-Prüfung hinzufügen
        if content is None:
            return None

        content_lower = content.lower()

        for workflow_name, workflow_data in workflows.items():
            steps = workflow_data.get("steps", [])
            if any(step.lower() in content_lower for step in steps):
                return steps[0]  # Gibt den ersten passenden Step zurück

        return None

    def _suggest_tags(self, content: str, note_type: str, template: str) -> List[str]:
        """Schlägt Tags basierend auf Content-Analyse vor."""
        tags = set()

        # Null-safety check for content
        if content is None:
            return []

        content_lower = content.lower()

        # Basis-Tags
        if "python" in content_lower:
            tags.add("python")

        # Framework-Tags
        if any(fw in content_lower for fw in ["django", "flask", "fastapi"]):
            tags.add("framework")
            tags.add("web-entwicklung")

        # Testing-Tags
        if any(test in content_lower for test in ["test", "pytest", "automation"]):
            tags.add("testing")
            tags.add("automation")

        # ML-Tags
        if any(ml in content_lower for ml in ["tensorflow", "pytorch", "machine learning", "ml"]):
            tags.add("machine-learning")
            tags.add("data-science")

        # Performance-Tags (NEW)
        # Performance Metrics
        if any(metric in content_lower for metric in ["performance", "benchmark", "timing", "metrics", "measurement", "profiling", "monitoring", "statistics", "latency", "throughput", "response time"]):
            tags.add("performance-metrics")

        # System Optimization
        if any(opt in content_lower for opt in ["optimization", "optimize", "performance tuning", "efficiency", "speed up", "memory usage", "cpu usage", "database optimization", "query optimization", "caching", "scaling"]):
            tags.add("system-optimization")

        # Command Tracking
        if any(cmd in content_lower for cmd in ["command", "execution", "tracking", "monitoring", "logging", "audit", "history", "terminal", "shell", "cli", "script execution", "process monitoring"]):
            tags.add("command-tracking")

        # Type-based Tags
        if note_type:
            tags.add(note_type)

        # Template-based Tags
        if template == "Python Framework":
            tags.add("framework")
        elif template == "Programmiersprache-Geschichte":
            tags.add("geschichte")

        return list(tags)

    def _suggest_tags_dynamic(
        self, content: str, note_type: str, template: str, templates: dict
    ) -> List[str]:
        """Schlägt Tags basierend auf dynamischer Analyse vor."""
        tags = set()

        # Null-Prüfung hinzufügen
        if content is None:
            return []

        content_lower = content.lower()

        # Dynamische Analyse der Templates
        for template_name, rules in templates.items():
            required_keywords = rules.get("content_standards", {}).get("required_keywords", [])
            optional_keywords = rules.get("content_standards", {}).get("optional_keywords", [])

            if any(kw in content_lower for kw in required_keywords):
                tags.add(template_name)
            if any(kw in content_lower for kw in optional_keywords):
                tags.add(template_name)

        return list(tags)

    def _check_potential_duplicate(self, name: str) -> bool:
        """Prüft auf potentielle Duplikate (vereinfacht)."""
        # Simuliere existierende Notes
        existing_notes = [
            "Python Geschichte",
            "Django Framework",
            "PyTest Framework",
            "Guido van Rossum",
            "Python Taschenrechner Beispiel",
        ]

        name_lower = name.lower()
        for existing in existing_notes:
            existing_lower = existing.lower()

            # Prüfe auf hohe Wort-Überlappung
            name_words = set(name_lower.split())
            existing_words = set(existing_lower.split())

            if name_words and existing_words:
                intersection = name_words.intersection(existing_words)
                if len(intersection) >= 2:  # Mindestens 2 gemeinsame Wörter
                    return True

        return False

    def _check_potential_duplicate_dynamic(self, name: str, threshold: float) -> bool:
        """Prüft auf potentielle Duplikate basierend auf Neo4j-Daten."""
        if not self.driver:
            return self._check_potential_duplicate_fallback(name, threshold)

        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (n:Note)
                    WHERE n.name <> $name
                    RETURN n.name as existing_name
                """,
                    name=name,
                )

                existing_notes = [record["existing_name"] for record in result]

                name_lower = name.lower()
                for existing in existing_notes:
                    existing_lower = existing.lower()

                    # Berechne Ähnlichkeit (Jaccard-Index)
                    name_set = set(name_lower.split())
                    existing_set = set(existing_lower.split())

                    if name_set and existing_set:
                        intersection = name_set.intersection(existing_set)
                        union = name_set.union(existing_set)
                        similarity = len(intersection) / len(union)

                        if similarity >= threshold:
                            return True
                return False

        except Exception as e:
            print(f"⚠️ Fehler bei Duplikat-Prüfung in Neo4j: {e}")
            return self._check_potential_duplicate_fallback(name, threshold)

    def _check_potential_duplicate_fallback(self, name: str, threshold: float) -> bool:
        """Fallback für Duplikat-Prüfung ohne Neo4j."""
        # Null-Prüfung hinzufügen
        if name is None:
            return False

        # Simuliere existierende Notes
        existing_notes = [
            "Python Geschichte",
            "Django Framework",
            "PyTest Framework",
            "Guido van Rossum",
            "Python Taschenrechner Beispiel",
        ]

        name_lower = name.lower()
        for existing in existing_notes:
            existing_lower = existing.lower()

            name_set = set(name_lower.split())
            existing_set = set(existing_lower.split())

            if name_set and existing_set:
                intersection = name_set.intersection(existing_set)
                union = name_set.union(existing_set)
                similarity = len(intersection) / len(union)

                if similarity >= threshold:
                    return True

        return False

    def load_validation_rules_from_neo4j(self):
        """Lädt Validierungsregeln aus Neo4j."""
        if not self.driver:
            return

        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (r:ValidationRule)
                    RETURN r.rule_name as rule_name, r.value as value, r.type as value_type
                """
                )

                neo4j_rules = {}
                for record in result:
                    rule_name = record["rule_name"]
                    value = record["value"]
                    value_type = record.get("value_type", "string")

                    # Konvertiere basierend auf Typ
                    if value_type == "boolean":
                        value = str(value).lower() == "true"
                    elif value_type == "integer":
                        value = int(value)
                    elif value_type == "float":
                        value = float(value)

                    neo4j_rules[rule_name] = value

                # Merge mit bestehenden Regeln
                if neo4j_rules:
                    self.config["validation_rules"].update(neo4j_rules)

        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Validierungsregeln aus Neo4j: {e}")

    def save_validation_rules_to_neo4j(self, rules: dict):
        """Speichert Validierungsregeln in Neo4j."""
        if not self.driver:
            return

        try:
            with self.driver.session() as session:
                for rule_name, value in rules.items():
                    # Bestimme Datentyp
                    if isinstance(value, bool):
                        value_type = "boolean"
                    elif isinstance(value, int):
                        value_type = "integer"
                    elif isinstance(value, float):
                        value_type = "float"
                    else:
                        value_type = "string"

                    session.run(
                        """
                        MERGE (r:ValidationRule {rule_name: $rule_name})
                        SET r.value = $value,
                            r.type = $value_type,
                            r.updated_at = timestamp()
                    """,
                        rule_name=rule_name,
                        value=str(value),
                        value_type=value_type,
                    )

        except Exception as e:
            print(f"⚠️ Fehler beim Speichern der Validierungsregeln in Neo4j: {e}")


def print_validation_result(result: ValidationResult, note_name: str):
    """Gibt Validierungsergebnis formatiert aus."""
    print(f"🔍 Validierung für Note: '{note_name}'")
    print("=" * 50)

    if result.errors:
        print("❌ Fehler:")
        for error in result.errors:
            print(f"   • {error}")

    if result.warnings:
        print("⚠️  Warnungen:")
        for warning in result.warnings:
            print(f"   • {warning}")

    if result.suggestions:
        print("💡 Empfehlungen:")
        for suggestion in result.suggestions:
            print(f"   • {suggestion}")

    if not result.errors and not result.warnings and not result.suggestions:
        print("✅ Perfekt - keine Probleme gefunden!")

    print()
    return result.passed


if __name__ == "__main__":
    # Test der Data Governance
    governance = DataGovernanceEngine()

    # Test 1: Gute Note
    print("🧪 Test 1: Gute Note")
    result = governance.validate_note_creation(
        name="FastAPI Framework",
        content="FastAPI ist ein modernes, schnelles Web-Framework für Python APIs. **Hauptmerkmale:** Hohe Performance, automatische API-Dokumentation. **Verwendung:** Wird von Microsoft und Uber verwendet. **Status:** Sehr beliebt in 2025.",
        description="Hochperformantes Python API-Framework",
        note_type="framework",
    )
    print_validation_result(result, "FastAPI Framework")

    # Test 2: Problematische Note
    print("🧪 Test 2: Problematische Note")
    result = governance.validate_note_creation(
        name="test", content="kurz", description="", note_type=""
    )
    print_validation_result(result, "test")
