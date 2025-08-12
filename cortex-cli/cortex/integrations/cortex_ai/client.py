"""Cortex AI Client"""

class CortexAIClient:
    def __init__(self, api_key=None):
        self.api_key = api_key
    
    def is_enabled(self):
        """Prüft, ob der AI-Client aktiviert und konfiguriert ist"""
        # Für Demo-Zwecke immer aktiviert, in echter Implementierung würde hier
        # die Konfiguration geprüft werden
        return True
    
    def chat(self, message, vault_id=1):
        """Chat mit dem AI-Client"""
        return {
            "message": f"AI Response to: {message} (Vault: {vault_id})",
            "links": [
                {"link_text": "Demo Link", "target_type": "note"}
            ]
        }
    
    def analyze(self, content):
        """Basis-Analyse (kompatibilität)"""
        return {"analysis": "Mock analysis result"}
    
    def analyze_content(self, content, source_path=None, vault_id=1):
        """Analysiert Inhalt und findet potentielle Verknüpfungen"""
        return {
            "analysis": f"Analysiert {len(content)} Zeichen" + (f" aus {source_path}" if source_path else ""),
            "confidence": 0.95,
            "keywords": ["demo", "test", "cortex"],
            "links": [
                {
                    "target_chat_id": "demo-123",
                    "link_text": "Demo Verknüpfung",
                    "target_type": "note", 
                    "confidence": 0.85,
                    "reason": "Thematische Ähnlichkeit"
                }
            ]
        }
    
    def validate_links(self):
        """Validiert alle Links im System"""
        return {
            "total_links": 15,
            "valid_links": 12,
            "invalid_links": 3,
            "broken_links": 3,
            "warnings": [
                {
                    "link_id": "link-001",
                    "source": "/workspaces/cortex-py/cortex/01-Projects/CORTEX-SYSTEM/README.md",
                    "target": "/workspaces/cortex-py/cortex/non-existent.md",
                    "issue": "Ziel nicht gefunden"
                },
                {
                    "link_id": "link-002", 
                    "source": "/workspaces/cortex-py/cortex/08-Docs/Pattern-Analysis.md",
                    "target": "/workspaces/cortex-py/cortex/99-Archive/old-file.md",
                    "issue": "Ziel ist archiviert"
                }
            ],
            "reason_counts": {
                "Ziel nicht gefunden": 2,
                "Ziel ist archiviert": 1
            },
            "suggestions": [
                "3 verwaiste Links gefunden - möglicherweise entfernen",
                "2 zirkuläre Referenzen entdeckt - prüfen Sie die Logik"
            ]
        }

def get_client(api_key=None):
    return CortexAIClient(api_key)
