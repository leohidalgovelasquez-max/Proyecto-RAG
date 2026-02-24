# 🤖 RAG Explorer: Inteligencia Artificial Personalizada

![RAG Explorer Banner](https://img.shields.io/badge/Status-Online-brightgreen) ![Python](https://img.shields.io/badge/Python-3.10+-blue) ![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688) ![Gemini](https://img.shields.io/badge/AI-Google_Gemini-4285F4)

**RAG Explorer** es una plataforma avanzada de **Generación Aumentada por Recuperación (RAG)** que permite transformar tus propios archivos PDF y de texto en una base de conocimientos consultable mediante Inteligencia Artificial de última generación.

---

## 🌟 Características Principales

- **🔍 Búsqueda Semántica de Alta Precisión**: Utiliza *Sentence Transformers* y *FAISS* (Facebook AI Similarity Search) para encontrar información relevante basándose en el significado, no solo en palabras clave.
- **📄 Soporte Multiformato**: Carga archivos `.txt` y documentos `.pdf` directamente en la carpeta de datos para expandir el conocimiento del sistema de forma automática.
- **🎨 Interfaz Web Premium**: Un dashboard moderno y receptivo diseñado con una estética profesional, modo oscuro y micro-animaciones.
- **🧠 Cerebro Dual (Gemini/OpenAI)**: Integración optimizada con **Google Gemini 1.5** (gratuito) y soporte opcional para **OpenAI GPT**.
- **🛠️ Panel de Inspección Interno**: Visualiza en tiempo real los fragmentos de texto recuperados y el prompt técnico generado para el LLM.

---

## 🛠️ Tecnologías Utilizadas

- **Backend**: Python 3.10+, FastAPI, Uvicorn.
- **IA y NLP**: Google Generative AI, Sentence Transformers, FAISS (Facebook AI), PyMuPDF (fitz).
- **Frontend**: HTML5, CSS3 (Glassmorphism), Vanilla JavaScript.
- **Cálculo Numérico**: NumPy.

---

## 📋 Requisitos Previos

Asegúrate de tener instaladas las siguientes dependencias:

```powershell
pip install fastapi uvicorn sentence-transformers faiss-cpu numpy google-generativeai pymupdf
```

---

## 🚀 Instalación y Puesta en Marcha

1. **Clonar/Descargar el proyecto** en tu ordenador.
2. **Preparar tus datos**: Coloca tus documentos `.pdf` o `.txt` dentro de la carpeta `/data`.
3. **Iniciar el servidor**:
   ```powershell
   python main.py
   ```
4. **Acceder a la interfaz**: Abre el navegador en [http://localhost:8000](http://localhost:8000).

---

## 📖 Manual de Uso

### 1. Configurar la Inteligencia Artificial
Para que el sistema redacte respuestas como un humano, obtén una **API Key gratuita** de [Google AI Studio](https://aistudio.google.com/app/apikey) y pégala en el panel lateral de la aplicación web.

### 2. Expandir el Conocimiento
Solo tienes que arrastrar nuevos archivos a la carpeta `data/` y refrescar la página. El sistema re-indexará automáticamente los documentos y el contador de "Documentos" subirá.

### 3. Realizar Consultas
Escribe cualquier pregunta sobre tus documentos. El sistema:
1. Analizará tus archivos.
2. Recuperará los fragmentos exactos que responden a tu duda.
3. Le pedirá a Gemini que redacte la respuesta final basándose en esa información.

---

## 🏗️ Estructura de Archivos

- `main.py`: Servidor API y gestor de la interfaz web.
- `rag_system.py`: Motor lógico (Embeddings, Chunking y Búsqueda Vectorial).
- `static/`: Contiene todo el código del frontend (HTML, CSS, JS).
- `data/`: Tu biblioteca de documentos de conocimiento.
- `vectordb/`: Almacén de la base de datos de vectores FAISS.

---

## 🔄 Evolución del Proyecto (Log de Desarrollo)

1.  **v1.0 (CLI)**: Implementación básica del motor RAG en consola con archivos de texto simple.
2.  **v2.0 (Web)**: Creación de la arquitectura cliente-servidor con FastAPI y diseño de la UI premium.
3.  **v3.0 (PDF Support)**: Integración de PyMuPDF para permitir que el sistema aprenda de manuales y libros técnicos.
4.  **v4.0 (Gemini Ready)**: Cambio de motor de lenguaje de OpenAI a Google Gemini para ofrecer una experiencia gratuita y potente, con detección automática de modelos regionales.

---

*Desarrollado con ❤️ para potenciar el acceso inteligente a la información.*
