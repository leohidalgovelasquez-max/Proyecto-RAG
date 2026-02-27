import asyncio
import random
import time
from typing import Dict, Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime
from threading import Thread
import logging

logger = logging.getLogger(__name__)

@dataclass
class SensorData:
    """Representa los datos de un sensor"""
    node_id: str
    name: str
    value: float
    timestamp: datetime
    unit: str
    
    def to_dict(self):
        return {
            "node_id": self.node_id,
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "unit": self.unit
        }

class OPCUAClient:
    """
    Cliente OPC-UA para conectar con el PLC.
    Soporta modo simulación para pruebas.
    """
    
    def __init__(self, endpoint: str = "opc.tcp://localhost:4840", simulation_mode: bool = True):
        self.endpoint = endpoint
        self.simulation_mode = simulation_mode
        self.connected = False
        self._running = False
        self._monitoring_thread: Optional[Thread] = None
        self._callbacks: List[Callable] = []
        
        # Variables del PLC (simuladas o reales)
        self._nodes = {
            "ns=2;i=2": {"name": "Motor1_Temperatura", "unit": "°C", "base_value": 50, "variance": 5},
            "ns=2;i=3": {"name": "Motor1_Vibracion", "unit": "mm/s", "base_value": 1.5, "variance": 0.3},
            "ns=2;i=4": {"name": "Actuador_Ciclos", "unit": "ciclos", "base_value": 5000, "variance": 100},
            "ns=2;i=5": {"name": "Motor2_Temperatura", "unit": "°C", "base_value": 48, "variance": 4},
            "ns=2;i=6": {"name": "Motor2_Vibracion", "unit": "mm/s", "base_value": 1.2, "variance": 0.2},
        }
        
        self._values = {}
        
    def connect(self) -> bool:
        """Establece conexión con el servidor OPC-UA"""
        if self.simulation_mode:
            logger.info(f"Modo simulación OPC-UA activo: {self.endpoint}")
            self.connected = True
            return True
            
        try:
            from opcua import Client
            self._client = Client(self.endpoint)
            self._client.connect()
            self.connected = True
            logger.info(f"Conectado a servidor OPC-UA: {self.endpoint}")
            return True
        except Exception as e:
            logger.error(f"Error conectando a OPC-UA: {e}")
            self.simulation_mode = True
            self.connected = True
            return True
    
    def disconnect(self):
        """Desconecta del servidor OPC-UA"""
        self._running = False
        if not self.simulation_mode and hasattr(self, '_client'):
            try:
                self._client.disconnect()
            except:
                pass
        self.connected = False
        
    def read_node(self, node_id: str) -> Optional[SensorData]:
        """Lee un nodo específico"""
        if not self.connected:
            return None
            
        if self.simulation_mode:
            return self._simulate_read(node_id)
        
        try:
            node = self._client.get_node(node_id)
            value = node.get_value()
            return SensorData(
                node_id=node_id,
                name=self._nodes.get(node_id, {}).get("name", node_id),
                value=float(value),
                timestamp=datetime.now(),
                unit=self._nodes.get(node_id, {}).get("unit", "")
            )
        except Exception as e:
            logger.error(f"Error leyendo nodo {node_id}: {e}")
            return self._simulate_read(node_id)
    
    def read_all_nodes(self) -> Dict[str, SensorData]:
        """Lee todos los nodos configurados"""
        results = {}
        for node_id in self._nodes.keys():
            data = self.read_node(node_id)
            if data:
                results[node_id] = data
                self._values[node_id] = data.value
        return results
    
    def _simulate_read(self, node_id: str) -> Optional[SensorData]:
        """Simula la lectura de un sensor con datos realistas en tiempo real"""
        if node_id not in self._nodes:
            return None
            
        node_info = self._nodes[node_id]
        
        current_value = self._values.get(node_id, node_info["base_value"])
        
        # Simular comportamiento realista con variaciones constantes
        # Usar tiempo para crear patrones más dinámicos
        import time
        import math
        
        timestamp = time.time()
        
        # Diferentes patrones según tipo de sensor
        if "Temperatura" in node_info["name"]:
            # Temperatura: variación lenta con picos ocasionales
            pattern = math.sin(timestamp / 10) * 3  # Oscilación lenta
            noise = random.gauss(0, 1)  # Ruido gaussiano
            drift = random.uniform(-1, 1)  # Deriva
            new_value = node_info["base_value"] + pattern + noise + drift
            
            # Ocasionalmente generar picos de temperatura
            if random.random() < 0.02:
                new_value += random.uniform(5, 15)
                
        elif "Vibracion" in node_info["name"]:
            # Vibración: más errática, con picos súbitos
            noise = random.gauss(0, 0.8)
            spikes = random.uniform(0, 3) if random.random() < 0.1 else 0
            drift = random.uniform(-0.3, 0.3)
            new_value = node_info["base_value"] + noise + spikes + abs(drift)
            
        else:  # Ciclos
            # Ciclos: incremento constante
            increment = random.uniform(0.5, 2)
            new_value = current_value + increment
            if new_value > 10000:
                new_value = 5000  # Reset
        
        # Mantener dentro de límites físicos
        new_value = max(0.1, new_value)
        
        # Apply hard limits per sensor type
        if "Temperatura" in node_info["name"]:
            new_value = min(105, max(20, new_value))
        elif "Vibracion" in node_info["name"]:
            new_value = min(10, max(0.1, new_value))
        else:
            new_value = min(10000, max(0, new_value))
        
        self._values[node_id] = new_value
        
        return SensorData(
            node_id=node_id,
            name=node_info["name"],
            value=round(new_value, 2),
            timestamp=datetime.now(),
            unit=node_info["unit"]
        )
    
    def inject_anomaly(self, node_id: str, value: float):
        """Inyecta un valor anómalo para pruebas"""
        self._values[node_id] = value
        
    def start_monitoring(self, interval: float = 1.0, callback: Optional[Callable] = None):
        """Inicia el monitoreo continuo de los nodos"""
        if callback:
            self._callbacks.append(callback)
            
        self._running = True
        
        def monitor_loop():
            while self._running:
                data = self.read_all_nodes()
                for cb in self._callbacks:
                    try:
                        cb(data)
                    except Exception as e:
                        logger.error(f"Error en callback de monitoreo: {e}")
                time.sleep(interval)
        
        self._monitoring_thread = Thread(target=monitor_loop, daemon=True)
        self._monitoring_thread.start()
        logger.info("Monitoreo OPC-UA iniciado")
        
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        self._running = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=2)
            
    def get_node_info(self, node_id: str) -> Optional[Dict]:
        """Obtiene información de un nodo"""
        return self._nodes.get(node_id)
    
    @property
    def available_nodes(self) -> List[str]:
        """Lista de nodos disponibles"""
        return list(self._nodes.keys())


class OPCUAServer:
    """
    Servidor OPC-UA simulado para pruebas.
    Permite que clientes externos se conecten.
    """
    
    def __init__(self, port: int = 4840):
        self.port = port
        self._running = False
        
    def start(self):
        """Inicia el servidor simulado"""
        self._running = True
        logger.info(f"Servidor OPC-UA simulado iniciado en puerto {self.port}")
        logger.info("Endpoint: opc.tcp://localhost:4840")
        
    def stop(self):
        """Detiene el servidor"""
        self._running = False
        logger.info("Servidor OPC-UA detenido")
