#!/usr/bin/env python3
"""
Sistema de Monitoreo Industrial con Agente IA Experto
=====================================================

Este sistema combina:
- OPC-UA: Captura de datos en tiempo real de PLCs industriales
- Detector de Anomalías: Identificación de valores fuera de rango
- Agente RAG: Diagnóstico inteligente basado en manuales e histórico
- Dashboard: Interfaz para operarios con chat de asistencia

Uso:
    python main.py

Requisitos:
    - Python 3.9+
    - Instalar dependencias: pip install -r requirements.txt
"""

import sys
import subprocess

def main():
    """Punto de entrada principal"""
    print("=" * 60)
    print("Sistema de Monitoreo Industrial con Agente IA Experto")
    print("=" * 60)
    print("\nIniciando dashboard...\n")
    
    try:
        # Ejecutar el dashboard de Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "src/dashboard/app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n\nDashboard detenido por el usuario.")
    except Exception as e:
        print(f"\nError al iniciar: {e}")
        print("\nAsegúrate de tener Streamlit instalado:")
        print("  pip install streamlit")

if __name__ == "__main__":
    main()
