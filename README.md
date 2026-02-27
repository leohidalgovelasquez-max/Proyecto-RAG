# Sistema de Monitoreo Industrial con Agente IA Experto

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red)
![License](https://img.shields.io/badge/License-MIT-green)

## Descripción

Sistema de monitoreo industrial en tiempo real que combina la lectura de datos vía OPC-UA con un agente de IA que actúa como "experto de guardia". El agente no solo detecta anomalías, sino que propone soluciones basadas en manuales técnicos e histórico de fallos.

Este proyecto fue desarrollado como demostración de la integración de tecnologías industriales con inteligencia artificial para el diagnóstico y mantenimiento predictivo.

### Características Principales

- 📡 **Integración OPC-UA**: Conexión a PLCs industriales para captura de datos en tiempo real
- 🚨 **Detección de Anomalías**: Monitoreo continuo con alertas automáticas y clasificación por severidad
- 🤖 **Agente RAG**: Diagnóstico inteligente usando Retrieval-Augmented Generation
- 💬 **Chat Interactivo**: Asistencia paso a paso para reparaciones con instrucciones de seguridad
- 📊 **Dashboard**: Visualización en tiempo real con gráficos y estadísticas
- 📋 **Historial**: Registro completo de anomalías y resoluciones

## Estructura del Proyecto

```
├── config/
│   └── settings.yaml           # Configuración del sistema
├── data/
│   ├── manuales/               # Manuales técnicos (PDF/TXT)
│   └── historico/             # Historial de reparaciones
├── src/
│   ├── opcua/
│   │   └── client.py          # Cliente OPC-UA
│   ├── rag/
│   │   └── agent.py           # Agente RAG con IA
│   ├── dashboard/
│   │   └── app.py             # Dashboard Streamlit
│   └── utils/
│       ├── config_loader.py   # Cargador de configuración
│       └── anomaly_detector.py # Detector de anomalías
├── .streamlit/
│   └── config.toml            # Configuración de Streamlit
├── main.py                     # Punto de entrada
├── requirements.txt           # Dependencias Python
├── LICENSE                    # Licencia MIT
└── README.md                  # Este archivo
```

## Instalación

### Prerrequisitos

- Python 3.9 o superior
- Windows/Linux/MacOS

### Pasos de Instalación

1. **Clonar el repositorio:**
```bash
git clone https://github.com/leohidalgovelasquez-max/proyecto_Asistente-Inteligente-de-Mantenimiento-Predictivo-y-Diagnostico-de-Averias.git
cd proyecto_Asistente-Inteligente-de-Mantenimiento-Predictivo-y-Diagnostico-de-Averias
```

2. **Crear entorno virtual (recomendado):**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Ejecutar el sistema:**
```bash
python main.py
```

O directamente con Streamlit:
```bash
streamlit run src/dashboard/app.py
```

5. **Acceder al dashboard:**
- Abrir navegador en: `http://localhost:8501`

## Uso del Sistema

### Panel de Monitoreo

1. **Conectar**: Presiona el botón "Conectar" en el sidebar
2. **Actualizar**: Presiona "Actualizar Valores" para obtener datos de los sensores
3. **Ver anomalías**: Las alertas aparecen automáticamente cuando se detectan valores fuera de rango

### Detección y Resolución de Anomalías

- **Inyectar anomalía**: Puedes probar el sistema inyectando anomalías de prueba desde el sidebar
- **Diagnosticar**: Genera informe completo del agente IA con solución recomendada
- **Resolver**: Marca la anomalía como resuelta

### Chat con el Agente IA

El agente puede responder preguntas como:
- "¿Cómo repararlo?" → Pasos detallados de reparación
- "¿Qué herramientas necesito?" → Lista de materiales y repuestos
- "¿Cuánto tiempo?" → Tiempo estimado de reparación
- "¿Seguridad?" → Instrucciones de seguridad importantes

## Tecnologías Utilizadas

- **Frontend/Dashboard**: Streamlit
- **Comunicación Industrial**: OPC-UA (asyncua)
- **IA/RAG**: LangChain, ChromaDB, HuggingFace Embeddings
- **Procesamiento de Datos**: Pandas, NumPy

## Configuración

### Configuración OPC-UA

Editar `config/settings.yaml` para cambiar el endpoint del servidor OPC-UA:
```yaml
OPCUA:
  endpoint: "opc.tcp://tu-servidor:4840"
  sampling_interval: 1.0
```

### Configuración de Streamlit

El archivo `.streamlit/config.toml` contiene la configuración del dashboard.

## Funcionamiento del Sistema

### 1. Captura de Datos (OPC-UA)
El sistema se conecta a un PLC mediante servidor OPC-UA para monitorizar:
- Temperatura de motores (°C)
- Vibraciones (mm/s)
- Ciclos de actuador

### 2. Detección de Anomalías
Cuando un valor sale del rango normal:
- Temperatura > 85°C → Crítico
- Temperatura 70-85°C → Alerta
- Vibración > 5.0 mm/s → Crítico
- Vibración 3-5 mm/s → Alerta

### 3. Agente IA (RAG)
El agente utiliza:
- **Manual técnico**: Consulta automática del manual de la máquina
- **Histórico**: Busca soluciones anteriores similares
- **Diagnóstico**: Genera informe con solución recomendada

## Contribuir

1. Fork el proyecto
2. Crear rama (`git checkout -b feature/nueva-caracteristica`)
3. Commit cambios (`git commit -am 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crear Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

---

⭐️ Si te gusta este proyecto, no olvides darle una estrella!
