import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import json
import sys
from pathlib import Path
import random

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.set_page_config(
    page_title="Sistema de Monitoreo Industrial - IA Experto",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Styles
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #0f3460;
    }
    .header-title {
        font-size: 24px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Inicialización de estados
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_anomaly' not in st.session_state:
    st.session_state.current_anomaly = None
if 'opcua_client' not in st.session_state:
    from src.opcua.client import OPCUAClient
    st.session_state.opcua_client = OPCUAClient(simulation_mode=True)
if 'rag_agent' not in st.session_state:
    from src.rag.agent import RAGAgent
    st.session_state.rag_agent = RAGAgent({
        "embeddings_model": "sentence-transformers/all-MiniLM-L6-v2",
        "manuales_path": "data/manuales",
        "historico_path": "data/historico",
        "chroma_persist_directory": "chroma_db"
    })
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = {}
if 'anomalies_list' not in st.session_state:
    st.session_state.anomalies_list = []
if 'sensor_history' not in st.session_state:
    st.session_state.sensor_history = []
if 'resolved_anomalies' not in st.session_state:
    st.session_state.resolved_anomalies = 0

# Configuración de sensores
SENSOR_CONFIG = {
    "Motor1_Temperatura": {"max": 85, "warn": 70, "unit": "C", "node": "ns=2;i=2"},
    "Motor2_Temperatura": {"max": 85, "warn": 70, "unit": "C", "node": "ns=2;i=5"},
    "Motor1_Vibracion": {"max": 5.0, "warn": 3.0, "unit": "mm/s", "node": "ns=2;i=3"},
    "Motor2_Vibracion": {"max": 5.0, "warn": 3.0, "unit": "mm/s", "node": "ns=2;i=6"},
    "Actuador_Ciclos": {"max": 10000, "warn": 8000, "unit": "ciclos", "node": "ns=2;i=4"}
}

def render_header():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(90deg, #1e3a5f, #2d5a87); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h1 style="color: white; margin: 0;">🏭 Sistema de Monitoreo Industrial</h1>
            <p style="color: #a0c4e8; margin: 5px 0 0 0;">Agente IA Experto de Guardia</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        active = len([a for a in st.session_state.anomalies_list if not a.get('resolved', False)])
        status_color = "🔴" if active > 0 else "🟢"
        st.metric("Estado", f"{status_color} {'Alerta' if active > 0 else 'Normal'}")
        st.caption(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

def render_metrics():
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        active = len([a for a in st.session_state.anomalies_list if not a.get('resolved', False)])
        st.metric("🚨 Anomalías Activas", active, delta_color="inverse" if active > 0 else "normal")
    
    with col2:
        critical = len([a for a in st.session_state.anomalies_list if a.get('severity') == 'critical'])
        st.metric("🔴 Críticas", critical)
    
    with col3:
        st.metric("✅ Resueltas", st.session_state.resolved_anomalies)
    
    with col4:
        st.metric("📊 Sensores", len(SENSOR_CONFIG))

def update_sensors():
    """Actualiza los datos de los sensores"""
    if not st.session_state.opcua_client.connected:
        st.session_state.opcua_client.connect()
    
    new_data = st.session_state.opcua_client.read_all_nodes()
    st.session_state.sensor_data = new_data
    
    if new_data:
        timestamp = datetime.now()
        for node_id, data in new_data.items():
            st.session_state.sensor_history.append({
                'timestamp': timestamp,
                'sensor': data.name,
                'value': data.value,
                'unit': data.unit
            })
        
        if len(st.session_state.sensor_history) > 200:
            st.session_state.sensor_history = st.session_state.sensor_history[-200:]
        
        check_anomalies(new_data)

def render_sensors():
    st.subheader("📊 Sensores en Tiempo Real")
    
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        if st.button("🔄 Actualizar Valores", type="primary", use_container_width=True):
            update_sensors()
            st.rerun()
    
    with col_info:
        st.caption("Presione el botón para actualizar los datos de los sensores")
    
    # Valores por defecto normales para cada sensor
    default_values = {
        "Motor1_Temperatura": 55.0,
        "Motor1_Vibracion": 1.5,
        "Actuador_Ciclos": 5000.0,
        "Motor2_Temperatura": 52.0,
        "Motor2_Vibracion": 1.2
    }
    
    # Crear diccionario de datos reales por nombre
    real_data = {}
    if st.session_state.sensor_data:
        for node_id, data in st.session_state.sensor_data.items():
            real_data[data.name] = data
    
    cols = st.columns(5)
    sensor_names = list(SENSOR_CONFIG.keys())
    
    for idx, name in enumerate(sensor_names):
        config = SENSOR_CONFIG[name]
        
        # Usar valor por defecto
        value = default_values.get(name, 50.0)
        unit = config["unit"]
        
        # Sobrescribir con datos reales si existen
        if name in real_data:
            data = real_data[name]
            value = data.value
            unit = data.unit
        
        with cols[idx]:
            if value > config["max"]:
                emoji = "🔴"
                status = "CRÍTICO"
            elif value > config["warn"]:
                emoji = "🟡"
                status = "ALERTA"
            else:
                emoji = "🟢"
                status = "Normal"
            
            st.metric(f"{emoji} {name}", f"{value:.1f} {unit}", status)

def check_anomalies(sensor_data):
    """Verifica y crea anomalías automáticamente"""
    counter = len(st.session_state.anomalies_list) + 1
    
    for node_id, data in sensor_data.items():
        name = data.name
        value = data.value
        config = SENSOR_CONFIG.get(name)
        
        if not config:
            continue
        
        # Verificar si ya existe anomalía activa
        exists = any(a.get('node_id') == node_id and not a.get('resolved', False) for a in st.session_state.anomalies_list)
        if exists:
            continue
        
        # Crear anomalía si supera el umbral
        if value > config["max"]:
            severity = "critical" if value > config["max"] * 1.1 else "warning"
            anomaly = {
                'id': f"ANOMALY_{counter:04d}",
                'node_id': node_id,
                'sensor_name': name,
                'value': value,
                'threshold_max': config["max"],
                'threshold_min': 0,
                'severity': severity,
                'message': f"Valor {value:.2f} excede el máximo {config['max']}",
                'timestamp': datetime.now().isoformat(),
                'resolved': False
            }
            st.session_state.anomalies_list.append(anomaly)
            counter += 1

def render_anomalies():
    st.subheader("🚨 Anomalías Detectadas")
    
    active = [a for a in st.session_state.anomalies_list if not a.get('resolved', False)]
    
    if not active:
        st.success("✅ Sistema operando normalmente - Sin anomalías activas")
        return
    
    st.error(f"⚠️ {len(active)} anomalía(s) detectada(s)")
    
    for idx, anomaly in enumerate(active):
        severity = "🔴" if anomaly.get('severity') == 'critical' else "🟡"
        anomaly_id = anomaly.get('id', 'UNKNOWN')
        
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
            
            with c1:
                st.markdown(f"**{severity} {anomaly.get('sensor_name', 'N/A')}**")
                st.caption(f"ID: {anomaly_id}")
            
            with c2:
                st.markdown(f"**Valor: {anomaly.get('value', 0):.2f}**")
                st.caption(f"Umbral máx: {anomaly.get('threshold_max', 0)}")
            
            with c3:
                st.markdown(f"_{anomaly.get('message', 'Sin mensaje')}_")
            
            with c4:
                c4a, c4b = st.columns(2)
                with c4a:
                    if st.button("📋 Diagnosticar", key=f"diag_{anomaly_id}_{idx}", use_container_width=True):
                        st.session_state.current_anomaly = anomaly
                        diagnose_anomaly(anomaly)
                        st.rerun()
                with c4b:
                    anomaly_id = anomaly.get('id')
                    if st.button("✅ Resolver", key=f"resolve_{anomaly_id}_{idx}", use_container_width=True):
                        # Buscar y marcar como resuelta
                        for i, a in enumerate(st.session_state.anomalies_list):
                            if a.get('id') == anomaly_id:
                                st.session_state.anomalies_list[i]['resolved'] = True
                                st.session_state.resolved_anomalies = st.session_state.resolved_anomalies + 1
                                st.success(f"Anomalía {anomaly_id} resuelta")
                                break
                        st.rerun()
            
            st.divider()

def diagnose_anomaly(anomaly):
    """Realiza el diagnóstico de una anomalía"""
    diagnosis = st.session_state.rag_agent.diagnose_anomaly(anomaly)
    report = st.session_state.rag_agent.generate_report(anomaly, diagnosis)
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": report
    })

def render_charts():
    st.subheader("📈 Análisis de Tendencias")
    
    if not st.session_state.sensor_history:
        st.info("No hay datos disponibles. Actualice los valores.")
        return
    
    df = pd.DataFrame(st.session_state.sensor_history)
    if df.empty:
        st.info("No hay datos")
        return
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    sensors = df['sensor'].unique()
    
    selected = st.multiselect("Seleccionar sensores", list(sensors), default=list(sensors)[:3])
    
    if selected:
        filtered = df[df['sensor'].isin(selected)]
        
        st.markdown("### Evolución Temporal")
        try:
            pivot = filtered.pivot_table(index='timestamp', columns='sensor', values='value', aggfunc='mean')
            if not pivot.empty:
                st.line_chart(pivot, height=250)
        except Exception as e:
            st.warning(f"Error al renderizar gráfico: {e}")
    
    st.markdown("### Estadísticas")
    if not df.empty:
        stats = df.groupby('sensor')['value'].agg(['count', 'mean', 'min', 'max', 'std']).round(2)
        stats.columns = ['Muestras', 'Media', 'Mín', 'Máx', 'Std']
        st.dataframe(stats, use_container_width=True)
    
    st.markdown("### Valores Actuales")
    if not df.empty:
        last_values = df.groupby('sensor')['value'].last()
        st.bar_chart(last_values, height=200)

def render_chat():
    st.subheader("💬 Asistente IA - Experto de Guardia")
    
    if st.session_state.current_anomaly:
        anomaly = st.session_state.current_anomaly
        st.info(f"📌 Contexto: {anomaly.get('sensor_name', 'N/A')} | Valor: {anomaly.get('value', 0):.2f}")
    
    for msg in st.session_state.messages[-10:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    if prompt := st.chat_input("Escriba su pregunta (ej: cómo repararlo, herramientas, seguridad, tiempo)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        context = None
        if st.session_state.current_anomaly:
            context = {"current_anomaly": st.session_state.current_anomaly}
        
        response = st.session_state.rag_agent.chat(prompt, context)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

def render_history():
    st.subheader("📋 Historial de Eventos")
    
    if not st.session_state.anomalies_list:
        st.info("No hay eventos registrados")
        return
    
    df = pd.DataFrame(st.session_state.anomalies_list)
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    c1, c2 = st.columns([3, 1])
    with c1:
        st.dataframe(df[['timestamp', 'sensor_name', 'value', 'severity', 'resolved']], use_container_width=True, hide_index=True)
    with c2:
        st.metric("Total", len(df))
        st.metric("Activas", len([a for a in df['resolved'] if not a]))
        st.metric("Resueltas", len([a for a in df['resolved'] if a]))

def render_sidebar():
    with st.sidebar:
        st.header("⚙️ Panel de Control")
        
        # Conexión
        st.header("📡 Conexión OPC-UA")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔌 Conectar", use_container_width=True):
                st.session_state.opcua_client.connect()
                # Resetear datos
                st.session_state.sensor_data = {}
                st.session_state.anomalies_list = []
                st.session_state.resolved_anomalies = 0
                st.session_state.messages = []
                st.session_state.current_anomaly = None
                # Obtener nuevos datos
                update_sensors()
                st.success("Conectado!")
        with c2:
            if st.button("🔴 Off", use_container_width=True, help="Desconectar"):
                st.session_state.opcua_client.disconnect()
        
        st.divider()
        
        # Inyectar anomalías
        st.header("🧪 Inyectar Anomalías")
        options = [
            "Ninguna",
            "Temperatura M1 > 95°C",
            "Temperatura M2 > 90°C",
            "Vibración M1 > 7.0",
            "Vibración M2 > 6.0",
            "Ciclos > 9500"
        ]
        selected = st.selectbox("Seleccionar", options, label_visibility="collapsed")
        
        if st.button("💉 Inyectar Anomalía", use_container_width=True):
            mappings = {
                "Temperatura M1 > 95°C": ("ns=2;i=2", 98.5),
                "Temperatura M2 > 90°C": ("ns=2;i=5", 92.0),
                "Vibración M1 > 7.0": ("ns=2;i=3", 7.5),
                "Vibración M2 > 6.0": ("ns=2;i=6", 6.5),
                "Ciclos > 9500": ("ns=2;i=4", 9800)
            }
            if selected in mappings:
                node_id, value = mappings[selected]
                st.session_state.opcua_client.inject_anomaly(node_id, value)
                update_sensors()
                st.success(f"Anomalía: {selected}")
        
        st.divider()
        
        # Opciones
        st.header("📊 Opciones")
        
        if st.button("🔄 Actualizar", use_container_width=True):
            update_sensors()
            st.rerun()
        
        if st.button("🗑️ Limpiar Todo", use_container_width=True):
            st.session_state.anomalies_list = []
            st.session_state.messages = []
            st.session_state.resolved_anomalies = 0
            st.success("Limpiado!")
        
        if st.button("📋 Nuevo Chat", use_container_width=True):
            st.session_state.current_anomaly = None
            st.session_state.messages = []
        
        st.divider()
        
        # Estadísticas
        total = len(st.session_state.anomalies_list)
        active = len([a for a in st.session_state.anomalies_list if not a.get('resolved', False)])
        critical = len([a for a in st.session_state.anomalies_list if a.get('severity') == 'critical'])
        
        st.metric("Total Eventos", total)
        st.metric("Activas", active)
        st.metric("Críticas", critical)
        
        st.divider()
        
        st.caption("Sistema de Monitoreo Industrial\nOPC-UA + RAG + IA")

def main():
    render_header()
    render_metrics()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📡 Monitoreo", "📈 Gráficos", "💬 Asistencia", "📋 Historial"])
    
    with tab1:
        render_sensors()
        render_anomalies()
    
    with tab2:
        render_charts()
    
    with tab3:
        render_chat()
    
    with tab4:
        render_history()
    
    render_sidebar()

if __name__ == "__main__":
    main()
