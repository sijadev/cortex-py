#!/usr/bin/env python3
"""
Advanced Pattern Detection for Cortex Learning Service
Implements sophisticated algorithms for pattern recognition across Cortex data
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, Counter
import hashlib

@dataclass
class Pattern:
    """Represents a detected pattern"""
    name: str
    confidence: float
    pattern_type: str
    context: Dict
    evidence: List[Dict]
    success_rate: float
    reuse_potential: float
    applicable_projects: List[str]
    detected_date: str
    
    def to_dict(self) -> Dict:
        return asdict(self)

class AdvancedPatternDetector:
    """Advanced pattern detection algorithms"""
    
    def __init__(self, cortex_path: Path):
        self.cortex_path = cortex_path
        self.patterns_cache = {}
        self.load_existing_patterns()
    
    def load_existing_patterns(self):
        """Load previously detected patterns"""
        patterns_file = self.cortex_path / "05-Insights"
        if patterns_file.exists():
            for pattern_file in patterns_file.glob("*Pattern*.md"):
                # Parse existing patterns for validation
                pass
    
    def detect_decision_patterns(self) -> List[Pattern]:
        """Detect patterns in decision-making processes"""
        patterns = []
        
        # Analyze all ADR files
        decisions_path = self.cortex_path / "03-Decisions"
        decisions = self._load_all_decisions(decisions_path)
        
        if len(decisions) >= 3:  # Minimum for pattern detection
            # 1. Confidence correlation patterns
            confidence_patterns = self._analyze_confidence_patterns(decisions)
            patterns.extend(confidence_patterns)
            
            # 2. Decision factor patterns
            factor_patterns = self._analyze_decision_factors(decisions)
            patterns.extend(factor_patterns)
            
            # 3. Timeline patterns
            timeline_patterns = self._analyze_timeline_patterns(decisions)
            patterns.extend(timeline_patterns)
            
            # 4. Success outcome patterns
            outcome_patterns = self._analyze_outcome_patterns(decisions)
            patterns.extend(outcome_patterns)
        
        return patterns
    
    def detect_project_patterns(self) -> List[Pattern]:
        """Detect patterns across different projects"""
        patterns = []
        
        projects_path = self.cortex_path / "01-Projects"
        projects = self._load_all_projects(projects_path)
        
        if len(projects) >= 2:  # Minimum for cross-project patterns
            # 1. Success factor patterns
            success_patterns = self._analyze_project_success_factors(projects)
            patterns.extend(success_patterns)
            
            # 2. Technology choice patterns
            tech_patterns = self._analyze_technology_patterns(projects)
            patterns.extend(tech_patterns)
            
            # 3. Workflow patterns
            workflow_patterns = self._analyze_workflow_patterns(projects)
            patterns.extend(workflow_patterns)
        
        return patterns
    
    def detect_ai_session_patterns(self) -> List[Pattern]:
        """Detect patterns in AI interaction sessions"""
        patterns = []
        
        neural_links_path = self.cortex_path / "02-Neural-Links"
        sessions = self._load_all_neural_links(neural_links_path)
        
        if len(sessions) >= 5:  # Minimum for AI pattern detection
            # 1. Effective query patterns
            query_patterns = self._analyze_query_effectiveness(sessions)
            patterns.extend(query_patterns)
            
            # 2. Insight quality patterns
            insight_patterns = self._analyze_insight_quality_patterns(sessions)
            patterns.extend(insight_patterns)
            
            # 3. Session structure patterns
            structure_patterns = self._analyze_session_structure_patterns(sessions)
            patterns.extend(structure_patterns)
        
        return patterns
    
    def _load_all_decisions(self, decisions_path: Path) -> List[Dict]:
        """Load and parse all decision files"""
        decisions = []
        
        for decision_file in decisions_path.rglob("ADR-*.md"):
            try:
                decision_data = self._parse_decision_file(decision_file)
                if decision_data:
                    decisions.append(decision_data)
            except Exception as e:
                print(f"Error parsing decision file {decision_file}: {e}")
        
        return decisions
    
    def _parse_decision_file(self, file_path: Path) -> Optional[Dict]:
        """Parse an ADR file and extract structured data"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract metadata using regex patterns
            decision_data = {
                'file_path': str(file_path),
                'filename': file_path.name,
                'created_date': datetime.fromtimestamp(file_path.stat().st_ctime),
                'modified_date': datetime.fromtimestamp(file_path.stat().st_mtime)
            }
            
            # Extract confidence score
            confidence_match = re.search(r'confidence[:\s]*`?(\d+\.?\d*)%?`?', content, re.IGNORECASE)
            if confidence_match:
                decision_data['confidence'] = float(confidence_match.group(1))
            
            # Extract status
            status_match = re.search(r'status[:\s]*`?([^`\n]+)`?', content, re.IGNORECASE)
            if status_match:
                decision_data['status'] = status_match.group(1).strip()
            
            # Extract decision type
            type_match = re.search(r'decision[_-]?type[:\s]*([^\n]+)', content, re.IGNORECASE)
            if type_match:
                decision_data['decision_type'] = type_match.group(1).strip()
            
            # Extract project context
            project_match = re.search(r'project[:\s]*\[\[([^\]]+)\]\]', content, re.IGNORECASE)
            if project_match:
                decision_data['project'] = project_match.group(1)
            
            # Extract reasoning quality indicators
            decision_data['has_benchmarks'] = bool(re.search(r'benchmark', content, re.IGNORECASE))
            decision_data['has_quantitative_data'] = bool(re.search(r'(\d+%|\d+\.\d+|\d+ms|\d+/\d+)', content))
            decision_data['options_considered'] = len(re.findall(r'option [abc123]', content, re.IGNORECASE))
            
            # Calculate content quality score
            decision_data['content_length'] = len(content)
            decision_data['section_count'] = len(re.findall(r'^##? ', content, re.MULTILINE))
            
            return decision_data
            
        except Exception as e:
            print(f"Error parsing decision file: {e}")
            return None
    
    def _analyze_confidence_patterns(self, decisions: List[Dict]) -> List[Pattern]:
        """Analyze patterns in confidence scoring"""
        patterns = []
        
        # Group decisions by confidence ranges
        confidence_groups = defaultdict(list)
        for decision in decisions:
            if 'confidence' in decision:
                conf = decision['confidence']
                if conf >= 90:
                    confidence_groups['high'].append(decision)
                elif conf >= 70:
                    confidence_groups['medium'].append(decision)
                else:
                    confidence_groups['low'].append(decision)
        
        # Analyze high-confidence decision patterns
        if len(confidence_groups['high']) >= 2:
            high_conf_factors = self._extract_success_factors(confidence_groups['high'])
            if high_conf_factors:
                pattern = Pattern(
                    name="High-Confidence-Decision-Factors",
                    confidence=0.85,
                    pattern_type="decision_quality",
                    context={
                        "confidence_range": "90%+",
                        "sample_size": len(confidence_groups['high'])
                    },
                    evidence=high_conf_factors,
                    success_rate=0.9,  # High confidence typically correlates with success
                    reuse_potential=0.8,
                    applicable_projects=["all"],
                    detected_date=datetime.now().isoformat()
                )
                patterns.append(pattern)
        
        return patterns
    
    def _extract_success_factors(self, decisions: List[Dict]) -> List[Dict]:
        """Extract common success factors from decisions"""
        factors = []
        
        # Common characteristics of successful/high-confidence decisions
        has_benchmarks = sum(1 for d in decisions if d.get('has_benchmarks', False))
        has_quantitative = sum(1 for d in decisions if d.get('has_quantitative_data', False))
        avg_options = sum(d.get('options_considered', 0) for d in decisions) / len(decisions)
        
        if has_benchmarks / len(decisions) > 0.7:
            factors.append({
                "factor": "benchmark_data_availability",
                "correlation": has_benchmarks / len(decisions),
                "description": "High-confidence decisions typically include benchmark data"
            })
        
        if has_quantitative / len(decisions) > 0.8:
            factors.append({
                "factor": "quantitative_evidence",
                "correlation": has_quantitative / len(decisions),
                "description": "Quantitative data strongly correlates with decision confidence"
            })
        
        if avg_options >= 2.5:
            factors.append({
                "factor": "multiple_options_considered",
                "correlation": avg_options / 5.0,  # Normalize to 0-1
                "description": f"Average {avg_options:.1f} options considered improves decision quality"
            })
        
        return factors
    
    def _load_all_projects(self, projects_path: Path) -> List[Dict]:
        """Load and parse all project files"""
        projects = []
        
        for project_file in projects_path.rglob("*.md"):
            if "workspace" in project_file.name.lower() or "project" in project_file.name.lower():
                try:
                    project_data = self._parse_project_file(project_file)
                    if project_data:
                        projects.append(project_data)
                except Exception as e:
                    print(f"Error parsing project file {project_file}: {e}")
        
        return projects
    
    def _parse_project_file(self, file_path: Path) -> Optional[Dict]:
        """Parse a project file and extract structured data"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            project_data = {
                'file_path': str(file_path),
                'filename': file_path.name,
                'created_date': datetime.fromtimestamp(file_path.stat().st_ctime),
                'project_path': str(file_path.parent)
            }
            
            # Extract project metadata
            name_match = re.search(r'project[_-]?name[:\s]*([^\n]+)', content, re.IGNORECASE)
            if name_match:
                project_data['name'] = name_match.group(1).strip()
            
            type_match = re.search(r'project[_-]?type[:\s]*([^\n]+)', content, re.IGNORECASE)
            if type_match:
                project_data['type'] = type_match.group(1).strip()
            
            status_match = re.search(r'status[:\s]*([^\n]+)', content, re.IGNORECASE)
            if status_match:
                project_data['status'] = status_match.group(1).strip()
            
            # Extract technology tags
            tech_tags = re.findall(r'#tech/([a-zA-Z0-9-]+)', content)
            project_data['technologies'] = tech_tags
            
            # Extract success indicators
            project_data['has_success_criteria'] = bool(re.search(r'success[_-]?criteria', content, re.IGNORECASE))
            project_data['has_metrics'] = bool(re.search(r'metric|kpi|measure', content, re.IGNORECASE))
            
            return project_data
            
        except Exception as e:
            print(f"Error parsing project file: {e}")
            return None
    
    def _analyze_technology_patterns(self, projects: List[Dict]) -> List[Pattern]:
        """Analyze technology choice patterns across projects"""
        patterns = []
        
        # Count technology usage
        tech_counter = Counter()
        for project in projects:
            for tech in project.get('technologies', []):
                tech_counter[tech] += 1
        
        # Find frequently used technologies
        total_projects = len(projects)
        frequent_techs = [(tech, count) for tech, count in tech_counter.items() 
                         if count / total_projects >= 0.5]  # Used in 50%+ of projects
        
        if frequent_techs:
            pattern = Pattern(
                name="Preferred-Technology-Stack",
                confidence=0.8,
                pattern_type="technology_choice",
                context={
                    "analysis_scope": "cross_project_technology_usage",
                    "sample_size": total_projects
                },
                evidence=[{
                    "technology": tech,
                    "usage_frequency": count / total_projects,
                    "projects_count": count
                } for tech, count in frequent_techs],
                success_rate=0.75,  # Estimated based on repeated usage
                reuse_potential=0.9,
                applicable_projects=["future_projects"],
                detected_date=datetime.now().isoformat()
            )
            patterns.append(pattern)
        
        return patterns
    
    def _load_all_neural_links(self, neural_links_path: Path) -> List[Dict]:
        """Load and parse all neural link session files"""
        sessions = []
        
        for session_file in neural_links_path.rglob("*.md"):
            try:
                session_data = self._parse_neural_link_file(session_file)
                if session_data:
                    sessions.append(session_data)
            except Exception as e:
                print(f"Error parsing neural link file {session_file}: {e}")
        
        return sessions
    
    def _parse_neural_link_file(self, file_path: Path) -> Optional[Dict]:
        """Parse a neural link file and extract session data"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            session_data = {
                'file_path': str(file_path),
                'filename': file_path.name,
                'created_date': datetime.fromtimestamp(file_path.stat().st_ctime)
            }
            
            # Extract session quality
            quality_match = re.search(r'session[_-]?quality[:\s]*([^\n]+)', content, re.IGNORECASE)
            if quality_match:
                quality_str = quality_match.group(1).strip().lower()
                if 'high' in quality_str or 'excellent' in quality_str:
                    session_data['quality_score'] = 9
                elif 'medium' in quality_str:
                    session_data['quality_score'] = 7
                elif 'low' in quality_str:
                    session_data['quality_score'] = 4
            
            # Count insights and queries
            session_data['insight_count'] = len(re.findall(r'insight[_-]?\d+', content, re.IGNORECASE))
            session_data['query_count'] = len(re.findall(r'query[_-]?\d+', content, re.IGNORECASE))
            
            # Extract session focus
            focus_match = re.search(r'session[_-]?focus[:\s]*([^\n]+)', content, re.IGNORECASE)
            if focus_match:
                session_data['focus'] = focus_match.group(1).strip()
            
            return session_data
            
        except Exception as e:
            print(f"Error parsing neural link file: {e}")
            return None
    
    def _analyze_query_effectiveness(self, sessions: List[Dict]) -> List[Pattern]:
        """Analyze effective AI query patterns"""
        patterns = []
        
        # Analyze high-quality sessions
        high_quality_sessions = [s for s in sessions if s.get('quality_score', 0) >= 8]
        
        if len(high_quality_sessions) >= 3:
            # Common characteristics of effective sessions
            avg_queries = sum(s.get('query_count', 0) for s in high_quality_sessions) / len(high_quality_sessions)
            avg_insights = sum(s.get('insight_count', 0) for s in high_quality_sessions) / len(high_quality_sessions)
            
            if avg_queries >= 2 and avg_insights >= 3:
                pattern = Pattern(
                    name="Effective-AI-Session-Structure",
                    confidence=0.82,
                    pattern_type="ai_interaction",
                    context={
                        "analysis_scope": "high_quality_ai_sessions",
                        "sample_size": len(high_quality_sessions)
                    },
                    evidence=[{
                        "factor": "optimal_query_count",
                        "value": avg_queries,
                        "description": f"Average {avg_queries:.1f} queries per effective session"
                    }, {
                        "factor": "insight_generation_rate",
                        "value": avg_insights,
                        "description": f"Average {avg_insights:.1f} insights per effective session"
                    }],
                    success_rate=0.85,
                    reuse_potential=0.9,
                    applicable_projects=["all"],
                    detected_date=datetime.now().isoformat()
                )
                patterns.append(pattern)
        
        return patterns
    
    def save_detected_patterns(self, patterns: List[Pattern]):
        """Save newly detected patterns to the insights directory"""
        insights_path = self.cortex_path / "05-Insights"
        insights_path.mkdir(exist_ok=True)
        
        for pattern in patterns:
            # Create a unique filename
            pattern_hash = hashlib.md5(pattern.name.encode()).hexdigest()[:8]
            filename = f"Auto-Detected-{pattern.name.replace(' ', '-')}-{pattern_hash}.md"
            file_path = insights_path / filename
            
            # Generate markdown content
            content = self._generate_pattern_markdown(pattern)
            
            with open(file_path, 'w') as f:
                f.write(content)
    
    def _generate_pattern_markdown(self, pattern: Pattern) -> str:
        """Generate markdown documentation for a detected pattern"""
        return f"""# Pattern: {pattern.name}

*Auto-detected by Cortex Learning Service*

## 📋 **Pattern-Metadata**
**Pattern-Name**: {pattern.name}  
**Confidence**: {pattern.confidence*100:.1f}%  
**Detection-Date**: {pattern.detected_date}  
**Pattern-Type**: {pattern.pattern_type}  
**Success-Rate**: {pattern.success_rate*100:.1f}%

## 🎯 **Pattern-Description**

### **Context**
{json.dumps(pattern.context, indent=2)}

### **Evidence**
{self._format_evidence(pattern.evidence)}

## ✅ **Applicability**

**Success-Rate**: {pattern.success_rate*100:.1f}%  
**Reuse-Potential**: {pattern.reuse_potential*100:.1f}%  
**Applicable-Projects**: {', '.join(pattern.applicable_projects)}

## 📊 **Pattern-Validation**

This pattern was automatically detected by analyzing {len(pattern.evidence)} data points with {pattern.confidence*100:.1f}% confidence.

---
**Tags**: #pattern-detected #auto-generated #confidence-{int(pattern.confidence*10):02d} #{pattern.pattern_type}

**Detection-Method**: Automated Pattern Recognition  
**Validation-Status**: Needs Human Review  
**Next-Action**: Manual validation and refinement recommended

---
*Auto-Generated Pattern Documentation | Cortex Learning Service v1.0*
"""
    
    def _format_evidence(self, evidence: List[Dict]) -> str:
        """Format evidence data for markdown display"""
        if not evidence:
            return "No specific evidence data available."
        
        formatted = []
        for i, item in enumerate(evidence, 1):
            formatted.append(f"{i}. **{item.get('factor', 'Unknown')}**: {item.get('description', 'No description')}")
            if 'correlation' in item:
                formatted.append(f"   - Correlation: {item['correlation']*100:.1f}%")
            if 'value' in item:
                formatted.append(f"   - Value: {item['value']}")
        
        return '\n'.join(formatted)

# Example usage for testing
if __name__ == "__main__":
    detector = AdvancedPatternDetector(Path("/Users/simonjanke/Projects/cortex"))
    
    # Detect patterns
    decision_patterns = detector.detect_decision_patterns()
    project_patterns = detector.detect_project_patterns()
    ai_patterns = detector.detect_ai_session_patterns()
    
    all_patterns = decision_patterns + project_patterns + ai_patterns
    
    print(f"Detected {len(all_patterns)} patterns:")
    for pattern in all_patterns:
        print(f"- {pattern.name} ({pattern.confidence*100:.1f}% confidence)")
    
    # Save patterns
    detector.save_detected_patterns(all_patterns)
