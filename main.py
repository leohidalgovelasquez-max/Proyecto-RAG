import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from rag_system import RAGSystem

app = FastAPI(title="RAG Visual Interface")

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar sistema RAG
rag = RAGSystem()
# Cargar datos e indexar
if os.path.exists("./data"):
    rag.load_documents("./data")
    rag.chunk_documents()
    rag.build_index()

import google.generativeai as genai

class QueryRequest(BaseModel):
    query: str
    api_key: str = None

@app.post("/api/query")
async def query_rag(request: QueryRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is empty")
    
    try:
        # 1. Recuperar fragmentos
        context_chunks = rag.retrieve(request.query)
        
        # 2. Generar el prompt
        prompt_with_context = rag.generate_response(request.query, context_chunks)
        
        final_answer = ""
        
        # 3. Intentar usar Google Gemini si hay clave
        if request.api_key:
            try:
                genai.configure(api_key=request.api_key)
                
                # BUSCAMOS AUTOMÁTICAMENTE QUÉ MODELO TIENES DISPONIBLE
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                if not available_models:
                    raise Exception("No se encontraron modelos disponibles para esta clave.")
                
                # Intentamos priorizar gemini-1.5-flash o pro
                selected_model = "models/gemini-1.5-flash" 
                if "models/gemini-1.5-flash" not in available_models:
                    selected_model = available_models[0] # Si no está flash, usamos el primero que haya
                
                model = genai.GenerativeModel(selected_model)
                response = model.generate_content(prompt_with_context)
                final_answer = response.text
                
            except Exception as e:
                final_answer = f"Error al conectar con Gemini: {str(e)}\n\n(Asegúrate de que la clave sea de Google AI Studio)"
        else:
            # Respuesta más limpia si no hay LLM
            final_answer = "🔍 INFO ENCONTRADA EN TUS DOCUMENTOS:\n\n"
            for i, chunk in enumerate(context_chunks):
                final_answer += f"Fragmento {i+1}:\n{chunk}\n\n"
            
            final_answer += "💡 *Nota: Introduce tu Gemini API Key en la izquierda para que la IA de Google redacte una respuesta.*"

        return {
            "query": request.query,
            "context": context_chunks,
            "prompt": prompt_with_context,
            "answer": final_answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status():
    return {
        "documents_loaded": len(rag.documents),
        "chunks_generated": len(rag.chunks),
        "index_ready": rag.index is not None
    }

# Servir archivos estáticos (esto debe ir al final)
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
