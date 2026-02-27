import yaml
import os
from pathlib import Path
from typing import Any, Dict

class Config:
    """Cargador de configuración del sistema"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Carga la configuración desde el archivo YAML"""
        config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración usando notación de puntos"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value
    
    @property
    def opcua(self) -> Dict:
        return self._config.get('OPCUA', {})
    
    @property
    def thresholds(self) -> Dict:
        return self._config.get('THRESHOLDS', {})
    
    @property
    def rag(self) -> Dict:
        return self._config.get('RAG', {})
    
    @property
    def dashboard(self) -> Dict:
        return self._config.get('DASHBOARD', {})

config = Config()
