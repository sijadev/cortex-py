"""
Cortex Configuration Manager
"""
import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

class CortexConfig:
    """
    Zentrales Configuration Management für Cortex CLI
    """
    
    def __init__(self, cortex_path: Optional[str] = None):
        """
        Initialisiert die Cortex-Konfiguration
        
        Args:
            cortex_path: Pfad zum Cortex-Vault (optional)
        """
        self.path = self.find_cortex_root(cortex_path or '.')
        self._config_cache = None
    
    @staticmethod
    def find_cortex_root(start_path: str = '.') -> Path:
        """
        Findet das Cortex-Root-Verzeichnis basierend auf Konfigurationsdateien
        
        Args:
            start_path: Startpfad für die Suche
            
        Returns:
            Path: Pfad zum Cortex-Root-Verzeichnis
        """
        current = Path(start_path).resolve()
        
        # Suche nach typischen Cortex-Indikatoren
        cortex_indicators = ['cortex.yaml', 'cortex.yml', '.cortex', '00-System']
        
        while current != current.parent:
            for indicator in cortex_indicators:
                if (current / indicator).exists():
                    return current
            current = current.parent
        
        # Fallback zum Start-Pfad falls nichts gefunden
        return Path(start_path).resolve()
    
    @property
    def config_file(self) -> Path:
        """
        Pfad zur Hauptkonfigurationsdatei
        
        Returns:
            Path: Pfad zur cortex.yaml
        """
        for config_name in ['cortex.yaml', 'cortex.yml']:
            config_path = self.path / config_name
            if config_path.exists():
                return config_path
        
        # Fallback: cortex.yaml erstellen
        return self.path / 'cortex.yaml'
    
    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Lädt die Cortex-Konfiguration
        
        Args:
            force_reload: Erzwingt das Neuladen der Konfiguration
            
        Returns:
            Dict: Konfigurationsdaten
        """
        if not force_reload and self._config_cache is not None:
            return self._config_cache
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
            except Exception as e:
                config = {'error': f'Fehler beim Laden der Konfiguration: {str(e)}'}
        else:
            config = self._create_default_config()
        
        self._config_cache = config
        return config
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Speichert die Cortex-Konfiguration
        
        Args:
            config: Zu speichernde Konfigurationsdaten
            
        Returns:
            bool: True bei Erfolg
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            self._config_cache = config
            return True
        except Exception:
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Holt einen Konfigurationswert
        
        Args:
            key: Konfigurationsschlüssel (unterstützt Dot-Notation)
            default: Standardwert falls Key nicht existiert
            
        Returns:
            Any: Konfigurationswert
        """
        config = self.load_config()
        
        # Unterstützung für Dot-Notation (z.B. 'ai.enabled')
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """
        Setzt einen Konfigurationswert
        
        Args:
            key: Konfigurationsschlüssel (unterstützt Dot-Notation)
            value: Zu setzender Wert
            
        Returns:
            bool: True bei Erfolg
        """
        config = self.load_config()
        
        # Unterstützung für Dot-Notation
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        
        return self.save_config(config)
    
    def _create_default_config(self) -> Dict[str, Any]:
        """
        Erstellt eine Standard-Konfiguration
        
        Returns:
            Dict: Standard-Konfiguration
        """
        return {
            'version': '1.0',
            'vault': {
                'name': 'Cortex System',
                'path': str(self.path),
                'created': str(Path.cwd())
            },
            'ai': {
                'enabled': False,
                'base_url': 'http://localhost:8000',
                'timeout': 30
            },
            'linking': {
                'auto_validate': True,
                'confidence_threshold': 0.7
            },
            'testing': {
                'auto_coverage': True,
                'coverage_threshold': 80
            }
        }
    
    @property
    def vault_name(self) -> str:
        """Name des Vaults"""
        return self.get('vault.name', 'Cortex System')
    
    @property  
    def is_ai_enabled(self) -> bool:
        """Ob AI-Integration aktiviert ist"""
        return self.get('ai.enabled', False)
    
    @property
    def ai_base_url(self) -> str:
        """AI-Service Base URL"""
        return self.get('ai.base_url', 'http://localhost:8000')
    
    def __str__(self) -> str:
        """String-Repräsentation"""
        return f"CortexConfig(path={self.path}, vault={self.vault_name})"
