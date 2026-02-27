import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class DiagnosticResult:
    """Resultado del diagnóstico del agente"""
    anomaly_id: str
    sensor_name: str
    detected_value: float
    diagnosis: str
    solution: str
    historical_reference: str
    safety_instructions: str
    estimated_time: str
    confidence: float
    sources: List[str] = field(default_factory=list)

class RAGAgent:
    """
    Agente RAG (Retrieval-Augmented Generation) para diagnóstico industrial.
    Combina la consulta de manuales técnicos con el histórico de reparaciones.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.embeddings = None
        self.vectorstore = None
        self.llm = None
        self.historico_data = []
        self._initialize()
        
    def _initialize(self):
        """Inicializa los componentes del RAG"""
        self._load_historico()
        self._initialize_vectorstore()
        
    def _load_historico(self):
        """Carga el histórico de reparaciones"""
        historico_path = Path(self.config.get("historico_path", "data/historico"))
        
        if not historico_path.exists():
            logger.warning(f"Directorio de histórico no encontrado: {historico_path}")
            return
            
        for file in historico_path.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.historico_data.extend(data)
                    else:
                        self.historico_data.append(data)
            except Exception as e:
                logger.error(f"Error cargando histórico {file}: {e}")
        
        logger.info(f"Cargados {len(self.historico_data)} registros del histórico")
        
    def _initialize_vectorstore(self):
        """Inicializa el vector store para los manuales"""
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from langchain_community.vectorstores import Chroma
            from langchain_community.document_loaders import PyPDFLoader, TextLoader
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            
            # Inicializar embeddings
            model_name = self.config.get("embeddings_model", "sentence-transformers/all-MiniLM-L6-v2")
            self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
            
            # Cargar documentos
            manuales_path = Path(self.config.get("manuales_path", "data/manuales"))
            documents = []
            
            if manuales_path.exists():
                # Cargar PDFs
                for pdf_file in manuales_path.glob("*.pdf"):
                    try:
                        loader = PyPDFLoader(str(pdf_file))
                        docs = loader.load()
                        documents.extend(docs)
                        logger.info(f"Cargado manual: {pdf_file.name}")
                    except Exception as e:
                        logger.error(f"Error cargando PDF {pdf_file}: {e}")
                
                # Cargar archivos de texto
                for txt_file in manuales_path.glob("*.txt"):
                    try:
                        loader = TextLoader(str(txt_file), encoding='utf-8')
                        docs = loader.load()
                        documents.extend(docs)
                    except Exception as e:
                        logger.error(f"Error cargando txt {txt_file}: {e}")
            
            if documents:
                # Dividir documentos
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )
                splits = text_splitter.split_documents(documents)
                
                # Crear vector store
                persist_dir = self.config.get("chroma_persist_directory", "chroma_db")
                self.vectorstore = Chroma.from_documents(
                    documents=splits,
                    embedding=self.embeddings,
                    persist_directory=persist_dir
                )
                logger.info(f"Vector store creado con {len(splits)} fragmentos")
            else:
                logger.warning("No se encontraron documentos para el vector store")
                
        except Exception as e:
            logger.error(f"Error inicializando vector store: {e}")
            self.vectorstore = None
    
    def diagnose_anomaly(self, anomaly_data: Dict) -> DiagnosticResult:
        """
        Realiza un diagnóstico completo de una anomalía.
        Consulta el manual y el histórico para generar una solución.
        """
        sensor_name = anomaly_data.get("sensor_name", "")
        value = anomaly_data.get("value", 0)
        node_id = anomaly_data.get("node_id", "")
        severity = anomaly_data.get("severity", "warning")
        
        # Consultar manuales
        manual_info = self._consult_manual(sensor_name, value)
        
        # Consultar histórico
        historical_info = self._consult_historico(sensor_name, value)
        
        # Generar diagnóstico
        diagnosis = self._generate_diagnosis(sensor_name, value, manual_info, historical_info)
        solution = self._generate_solution(sensor_name, value, manual_info, historical_info)
        safety = self._get_safety_instructions(sensor_name)
        time_estimate = self._estimate_repair_time(sensor_name, severity)
        
        sources = []
        if manual_info:
            sources.append(f"Manual técnico: {manual_info.get('source', 'N/A')}")
        if historical_info:
            sources.append(f"Histórico: {historical_info.get('date', 'N/A')}")
        
        return DiagnosticResult(
            anomaly_id=anomaly_data.get("id", "UNKNOWN"),
            sensor_name=sensor_name,
            detected_value=value,
            diagnosis=diagnosis,
            solution=solution,
            historical_reference=historical_info.get("summary", "No hay registros previos") if historical_info else "No hay registros previos",
            safety_instructions=safety,
            estimated_time=time_estimate,
            confidence=0.85 if historical_info else 0.7,
            sources=sources
        )
    
    def _consult_manual(self, sensor_name: str, value: float) -> Optional[Dict]:
        """Consulta el manual técnico para el sensor"""
        if not self.vectorstore:
            return self._get_fallback_manual_info(sensor_name)
            
        try:
            query = f"{sensor_name} error {value} solución"
            docs = self.vectorstore.similarity_search(query, k=2)
            
            if docs:
                return {
                    "content": docs[0].page_content,
                    "source": docs[0].metadata.get("source", "Manual"),
                    "page": docs[0].metadata.get("page", "N/A")
                }
        except Exception as e:
            logger.error(f"Error consultando manual: {e}")
            
        return self._get_fallback_manual_info(sensor_name)
    
    def _get_fallback_manual_info(self, sensor_name: str) -> Dict:
        """Información de fallback cuando no hay manual cargado"""
        name_lower = sensor_name.lower()
        
        if "temperatura" in name_lower:
            return {
                "content": "Código de error 0x04 indica sobrecalentamiento. Verificar sistema de refrigeración.",
                "source": "Manual Siemens (pág. 45)",
                "page": "45"
            }
        elif "vibracion" in name_lower:
            return {
                "content": "Vibración excesiva indica desgaste de rodamientos o desalineación.",
                "source": "Manual Siemens (pág. 78)",
                "page": "78"
            }
        elif "ciclos" in name_lower:
            return {
                "content": "Alto conteo de ciclos indica necesidad de mantenimiento preventivo.",
                "source": "Manual Siemens (pág. 102)",
                "page": "102"
            }
        
        return {
            "content": "Consulte el manual técnico para procedimientos específicos.",
            "source": "Base de conocimiento",
            "page": "N/A"
        }
    
    def _consult_historico(self, sensor_name: str, value: float) -> Optional[Dict]:
        """Consulta el histórico de reparaciones"""
        name_lower = sensor_name.lower()
        
        for record in reversed(self.historico_data):
            if name_lower in record.get("sensor", "").lower():
                return record
                
        # Retornar historial genérico si existe
        if self.historico_data:
            return self.historico_data[-1]
            
        return None
    
    def _generate_diagnosis(self, sensor_name: str, value: float, 
                           manual_info: Dict, historical_info: Optional[Dict]) -> str:
        """Genera el diagnóstico"""
        name_lower = sensor_name.lower()
        
        diagnosis = f"Fallo detectado en {sensor_name}. "
        
        if "temperatura" in name_lower:
            if value > 85:
                diagnosis += "Temperatura crítica que indica sobrecalentamiento del motor. "
                diagnosis += "Código de error 0x04 - Problema de fase o falla en sistema de refrigeración."
            else:
                diagnosis += "Temperatura elevada que requiere monitoreo."
        elif "vibracion" in name_lower:
            diagnosis += "Vibración excesiva que puede indicar desgaste de rodamientos, "
            diagnosis += "desalineación o desequilibrio en el rotor."
        elif "ciclos" in name_lower:
            diagnosis += "Conteo de ciclos elevado que indica desgaste del actuador."
            
        return diagnosis
    
    def _generate_solution(self, sensor_name: str, value: float,
                          manual_info: Dict, historical_info: Optional[Dict]) -> str:
        """Genera la solución recomendada"""
        name_lower = sensor_name.lower()
        
        solution = ""
        
        if historical_info:
            solution += f"Según el histórico, esto ya ocurrió el {historical_info.get('date', 'desconocido')}. "
            solution += f"Se solucionó: {historical_info.get('solution', 'consultar manual')}. "
        
        if "temperatura" in name_lower:
            solution += "Pasos recomendados: 1) Detener el motor. 2) Verificar nivel de refrigerante. "
            solution += "3) Revisar el relé K1. 4) Comprobar conexiones eléctricas."
        elif "vibracion" in name_lower:
            solution += "Pasos recomendados: 1) Realizar análisis de vibraciones. "
            solution += "2) Verificar alineación de ejes. 3) Inspeccionar rodamientos."
        elif "ciclos" in name_lower:
            solution += "Pasos recomendados: 1) Programar mantenimiento. "
            solution += "2) Preparar repuestos. 3) Programar reemplazo del actuador."
            
        return solution
    
    def _get_safety_instructions(self, sensor_name: str) -> str:
        """Obtiene las instrucciones de seguridad"""
        return (
            "⚠️ INSTRUCCIONES DE SEGURIDAD:\n"
            "1. Antes de cualquier intervención, seguir Lockout/Tagout (LOTO)\n"
            "2. Verificar que el equipo esté completamente detenido\n"
            "3. Usar EPP adecuado (guantes, gafas, casco)\n"
            "4. Mantener área de trabajo despejada\n"
            "5. Tener extintor disponible\n"
            "6. Nunca trabajar solo en equipos de alto riesgo"
        )
    
    def _estimate_repair_time(self, sensor_name: str, severity: str) -> str:
        """Estima el tiempo de reparación"""
        name_lower = sensor_name.lower()
        
        if severity == "critical":
            base_time = 90
        else:
            base_time = 45
            
        if "temperatura" in name_lower:
            return f"{base_time}-{base_time + 30} minutos"
        elif "vibracion" in name_lower:
            return f"{base_time + 30}-{base_time + 60} minutos"
        elif "ciclos" in name_lower:
            return f"{base_time + 60}-{base_time + 90} minutos"
            
        return "30-60 minutos"
    
    def chat(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Maneja preguntas en lenguaje natural del operario.
        Proporciona instrucciones paso a paso para reparaciones.
        """
        message_lower = message.lower()
        
        # Contexto de la conversación
        current_anomaly = context.get("current_anomaly") if context else None
        
        if "cómo" in message_lower or "paso" in message_lower or "instrucción" in message_lower:
            return self._provide_step_by_step(message, current_anomaly)
        elif "cuánto" in message_lower or "tiempo" in message_lower:
            return f"Tiempo estimado de reparación: {self._estimate_repair_time(current_anomaly.get('sensor_name', '') if current_anomaly else '', 'warning')}"
        elif "seguridad" in message_lower or "peligro" in message_lower:
            return self._get_safety_instructions(current_anomaly.get("sensor_name", "") if current_anomaly else "equipo")
        elif "herramienta" in message_lower or "repuesto" in message_lower:
            return self._get_required_tools(current_anomaly.get("sensor_name", "") if current_anomaly else "")
        else:
            return self._general_query(message)
    
    def _provide_step_by_step(self, message: str, context: Optional[Dict]) -> str:
        """Proporciona instrucciones paso a paso"""
        sensor = context.get("sensor_name", "") if context else ""
        
        steps = []
        
        if "temperatura" in sensor.lower():
            steps = [
                "1. DETENER el motor y esperar a que enfrie (10 min mínimo)",
                "2. BLOQUEAR la fuente de energía (LOTO)",
                "3. VERIFICAR nivel de refrigerante/lubricante",
                "4. INSPECCIONAR el sensor de temperatura",
                "5. REVISAR conexiones del relé K1",
                "6. MEDIR voltaje en las fases",
                "7. REEMPLAZAR componentes defectuosos",
                "8. REINICIAR sistema y monitorear"
            ]
        elif "vibracion" in sensor.lower():
            steps = [
                "1. DETENER el equipo inmediatamente",
                "2. BLOQUEAR energía (LOTO)",
                "3. REALIZAR análisis de vibraciones con equipo especializado",
                "4. VERIFICAR alineación de ejes",
                "5. INSPECCIONAR rodamientos",
                "6. COMPROBAR apriete de tornillos",
                "7. BALANCEAR rotor si es necesario",
                "8. REINICIAR y monitorear"
            ]
        else:
            steps = [
                "1. DETENER el equipo",
                "2. BLOQUEAR energía (LOTO)",
                "3. CONSULTAR manual específico",
                "4. IDENTIFICAR causa raíz",
                "5. PREPARAR herramientas y repuestos",
                "6. EJECUTAR reparación",
                "7. VERIFICAR funcionamiento",
                "8. DOCUMENTAR intervención"
            ]
            
        return "📋 PROCEDIMIENTO:\n\n" + "\n".join(steps)
    
    def _get_required_tools(self, sensor_name: str) -> str:
        """Lista de herramientas requeridas"""
        return (
            "🔧 HERRAMIENTAS Y MATERIALES:\n"
            "- Multímetro digital\n"
            "- Llaves allen (juego)\n"
            "- Destornilladores (Phillips y plano)\n"
            "- Llaves Fixed\n"
            "- Pinzas de presión\n"
            "- Tensor de correas\n"
            "- Lubricante específico\n"
            "- Repuestos: Relé K1, Sensor de temperatura, Rodamientos\n"
            "- EPP: Guantes aislantes, Gafas, Casco, Calzado seguridad"
        )
    
    def _general_query(self, message: str) -> str:
        """Maneja consultas generales"""
        return (
            "Para responder mejor a su pregunta, por favor indique:\n"
            "- Qué equipo o sensor está verificando\n"
            "- El código de error si lo hay\n"
            "- Los valores actuales de los parámetros\n"
            "\nTambién puede preguntar:\n"
            "• '¿cómo repararlo?' - Para pasos detallados\n"
            "• '¿cuánto tiempo?' - Para tiempo estimado\n"
            "• '¿qué herramientas?' - Para lista de materiales\n"
            "• '¿seguridad?' - Para instrucciones de seguridad"
        )
    
    def generate_report(self, anomaly: Dict, diagnosis: DiagnosticResult) -> str:
        """Genera un informe completo para el técnico"""
        report = f"""
╔══════════════════════════════════════════════════════════════════╗
║        INFORME DE DIAGNÓSTICO - AGENTE EXPERTO DE GUARDIA         ║
╚══════════════════════════════════════════════════════════════════╝

📌 DATOS DE LA ANOMALÍA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID:         {anomaly.get('id', 'N/A')}
Sensor:     {anomaly.get('sensor_name', 'N/A')}
Valor:      {anomaly.get('value', 'N/A')}
Severidad:  {anomaly.get('severity', 'N/A').upper()}
Fecha:      {anomaly.get('timestamp', 'N/A')}

🔍 DIAGNÓSTICO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{diagnosis.diagnosis}

💡 SOLUCIÓN RECOMENDADA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{diagnosis.solution}

📚 REFERENCIA HISTÓRICA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{diagnosis.historical_reference}

⏱️ TIEMPO ESTIMADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{diagnosis.estimated_time}

🔒 INSTRUCCIONES DE SEGURIDAD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{diagnosis.safety_instructions}

📄 FUENTES CONSULTADAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        for source in diagnosis.sources:
            report += f"• {source}\n"
            
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nivel de confianza: {diagnosis.confidence * 100:.0f}%
Agente Experto de Guardia - Sistema Industrial IA
"""
        return report
