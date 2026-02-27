from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Callable
from enum import Enum
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class SeverityLevel(Enum):
    """Niveles de severidad de las anomalías"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class Anomaly:
    """Representa una anomalía detectada"""
    id: str
    node_id: str
    sensor_name: str
    value: float
    threshold_min: float
    threshold_max: float
    severity: SeverityLevel
    message: str
    timestamp: datetime
    recommended_action: str = ""
    resolved: bool = False
    
    def to_dict(self):
        return {
            "id": self.id,
            "node_id": self.node_id,
            "sensor_name": self.sensor_name,
            "value": self.value,
            "threshold_min": self.threshold_min,
            "threshold_max": self.threshold_max,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "recommended_action": self.recommended_action,
            "resolved": self.resolved
        }

class AnomalyDetector:
    """
    Detector de anomalías basado en umbrales configurables.
    Monitorea los valores de los sensores y detecta cuando salen de rango.
    """
    
    def __init__(self, thresholds: Dict):
        self.thresholds = thresholds
        self._anomalies: List[Anomaly] = []
        self._callbacks: List[Callable] = []
        self._last_values: Dict[str, float] = {}
        self._anomaly_counter = 0
        
    def add_callback(self, callback: Callable):
        """Agrega un callback para cuando se detecta una anomalía"""
        self._callbacks.append(callback)
        
    def check_value(self, node_id: str, sensor_name: str, value: float, unit: str = "") -> Optional[Anomaly]:
        """Verifica si un valor está fuera de los umbrales"""
        
        # Ya hay una anomalía activa para este nodo?
        for existing in self._anomalies:
            if not existing.resolved and existing.node_id == node_id:
                return None  # Ya existe anomalía activa, no crear otra
        
        # Determinar el tipo de sensor basado en el nombre
        sensor_type = self._get_sensor_type(sensor_name)
        
        if sensor_type not in self.thresholds:
            return None
            
        threshold_config = self.thresholds[sensor_type]
        
        # Verificar umbrales
        threshold_min = threshold_config.get(f"{sensor_type}_min", 
                                               threshold_config.get("temperatura_min", 0))
        threshold_max = threshold_config.get(f"{sensor_type}_max", 
                                               threshold_config.get(f"{sensor_type}_max", 999))
        
        # Manejar casos especiales
        if "temperatura" in sensor_name.lower():
            threshold_min = threshold_config.get("temperatura_min", 0)
            threshold_max = threshold_config.get("temperatura_max", 100)
        elif "vibracion" in sensor_name.lower():
            threshold_max = threshold_config.get("vibracion_max", 10)
            threshold_min = 0
        elif "ciclos" in sensor_name.lower():
            threshold_max = threshold_config.get("ciclos_max", 10000)
            threshold_min = 0
            
        # Determinar severidad
        is_critical = self._is_critical_anomaly(value, threshold_min, threshold_max)
        severity = SeverityLevel.CRITICAL if is_critical else SeverityLevel.WARNING
        
        # Solo crear anomalía si está fuera de los umbrales
        if value > threshold_max:
            self._anomaly_counter += 1
            anomaly = Anomaly(
                id=f"ANOMALY_{self._anomaly_counter:04d}",
                node_id=node_id,
                sensor_name=sensor_name,
                value=value,
                threshold_min=threshold_min,
                threshold_max=threshold_max,
                severity=severity,
                message=f"Valor {value:.2f} {unit} excede el máximo ({threshold_max} {unit})",
                timestamp=datetime.now(),
                recommended_action=self._get_recommended_action(sensor_name, value, "HIGH")
            )
            self._anomalies.append(anomaly)
            self._notify_callbacks(anomaly)
            return anomaly
            
        elif value < threshold_min and threshold_min > 0:
            self._anomaly_counter += 1
            anomaly = Anomaly(
                id=f"ANOMALY_{self._anomaly_counter:04d}",
                node_id=node_id,
                sensor_name=sensor_name,
                value=value,
                threshold_min=threshold_min,
                threshold_max=threshold_max,
                severity=severity,
                message=f"Valor {value:.2f} {unit} está por debajo del mínimo ({threshold_min} {unit})",
                timestamp=datetime.now(),
                recommended_action=self._get_recommended_action(sensor_name, value, "LOW")
            )
            self._anomalies.append(anomaly)
            self._notify_callbacks(anomaly)
            return anomaly
            
        # Guardar valor si está en rango normal
        self._last_values[node_id] = value
        return None
    
    def _get_sensor_type(self, sensor_name: str) -> str:
        """Determina el tipo de sensor basado en su nombre"""
        name_lower = sensor_name.lower()
        if "temperatura" in name_lower:
            return "motor"
        elif "vibracion" in name_lower:
            return "motor"
        elif "ciclos" in name_lower:
            return "actuador"
        return "unknown"
    
    def _is_critical_anomaly(self, value: float, min_val: float, max_val: float) -> bool:
        """Determina si la anomalía es crítica"""
        if max_val > 0:
            deviation = abs(value - max_val) / max_val
            return deviation > 0.25  # 25% de desviación
        return False
    
    def _get_recommended_action(self, sensor_name: str, value: float, direction: str) -> str:
        """Genera una acción recomendada basada en el tipo de sensor"""
        name_lower = sensor_name.lower()
        
        if "temperatura" in name_lower:
            if direction == "HIGH":
                return "Verificar sistema de refrigeración. Revisar niveles de aceite. Comprobar carga del motor."
            else:
                return "Verificar sensor de temperatura. Posible fault en termopar."
        elif "vibracion" in name_lower:
            return "Realizar análisis de vibraciones. Verificar rodamientos y alineación."
        elif "ciclos" in name_lower:
            return "Programar mantenimiento preventivo. Preparar reemplazo del actuador."
        
        return "Consultar manual técnico para procedimientos específicos."
    
    def _notify_callbacks(self, anomaly: Anomaly):
        """Notifica a todos los callbacks registrados"""
        for callback in self._callbacks:
            try:
                callback(anomaly)
            except Exception as e:
                logger.error(f"Error en callback de anomalía: {e}")
    
    def get_active_anomalies(self) -> List[Anomaly]:
        """Retorna las anomalías activas (no resueltas)"""
        return [a for a in self._anomalies if not a.resolved]
    
    def get_all_anomalies(self) -> List[Anomaly]:
        """Retorna todas las anomalías"""
        return self._anomalies
    
    def resolve_anomaly(self, anomaly_id: str):
        """Marca una anomalía como resuelta"""
        for anomaly in self._anomalies:
            if anomaly.id == anomaly_id:
                anomaly.resolved = True
                logger.info(f"Anomalía {anomaly_id} marcada como resuelta")
                break
    
    def get_anomaly_history(self, limit: int = 50) -> List[Dict]:
        """Retorna el historial de anomalías"""
        return [a.to_dict() for a in self._anomalies[-limit:]]
    
    def save_history(self, filepath: str):
        """Guarda el historial de anomalías a un archivo"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.get_anomaly_history(limit=1000), f, indent=2, ensure_ascii=False)
    
    def clear_resolved(self):
        """Limpia las anomalías resueltas"""
        self._anomalies = [a for a in self._anomalies if not a.resolved]
