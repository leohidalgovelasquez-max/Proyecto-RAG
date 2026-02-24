import os
import glob
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

class RAGSystem:
    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        """
        Inicializa el sistema RAG con un modelo de embeddings multilingüe.
        """
        print(f"Cargando modelo de embeddings: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.documents = []
        self.chunks = []

    def load_documents(self, directory_path):
        """
        Carga archivos de texto (.txt) y PDF desde el directorio especificado.
        """
        import fitz  # PyMuPDF
        
        # Cargar archivos TXT
        txt_files = glob.glob(os.path.join(directory_path, "*.txt"))
        for file_path in txt_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.documents.append(f.read())
        
        # Cargar archivos PDF
        pdf_files = glob.glob(os.path.join(directory_path, "*.pdf"))
        for file_path in pdf_files:
            try:
                doc = fitz.open(file_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                self.documents.append(text)
                print(f"PDF Cargado: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Error al cargar PDF {file_path}: {e}")
                
        print(f"Total: {len(self.documents)} documentos cargados.")

    def chunk_documents(self, chunk_size=500):
        """
        Divide los documentos de forma inteligente por párrafos o frases,
        evitando cortar palabras por la mitad.
        """
        self.chunks = []
        for doc in self.documents:
            # Dividimos por párrafos (doble salto de línea) para mantener el sentido
            paragraphs = doc.split('\n\n')
            for p in paragraphs:
                if len(p) > 0:
                    self.chunks.append(p.strip())
        
        print(f"Generados {len(self.chunks)} fragmentos coherentes.")

    def build_index(self):
        """
        Crea el índice vectorial FAISS a partir de los fragmentos.
        """
        if not self.chunks:
            print("AVISO: No se encontraron fragmentos para indexar.")
            return

        print("Generando vectores semánticos (embeddings)... por favor espera.")
        try:
            embeddings = self.model.encode(self.chunks)
            embeddings_np = np.array(embeddings).astype('float32')
            dimension = embeddings_np.shape[1]
            
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings_np)
            print(f"ÉXITO: Índice vectorial construido con {len(self.chunks)} fragmentos.")
        except Exception as e:
            print(f"ERROR al construir el índice: {e}")

    def retrieve(self, query, k=2):
        """
        Recupera los K fragmentos más similares a la consulta.
        """
        if self.index is None:
            return "Error: El índice no ha sido construido."

        query_vector = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_vector).astype('float32'), k)
        
        results = [self.chunks[idx] for idx in indices[0]]
        return results

    def generate_response(self, query, context):
        """
        Simula la generación de una respuesta usando el contexto.
        En un entorno real, aquí se llamaría a un LLM (como GPT-4).
        """
        context_str = "\n---\n".join(context)
        
        # PROMPT DEL SISTEMA
        system_prompt = f"""
        Eres un asistente inteligente experto en búsqueda y análisis de documentos. 
        Tu misión es responder basándote en el CONTEXTO que te proporciono abajo.
        
        REGLAS:
        1. Si la respuesta está en el contexto, redacta una respuesta clara y profesional.
        2. Si no encuentras la respuesta específica, intenta usar la información disponible para dar una pista o explica amablemente que no tienes documentos sobre ese tema específico todavía.
        3. Siempre sé amable y servicial.
        
        CONTEXTO:
        {context_str}
        
        PREGUNTA DEL USUARIO: {query}
        
        RESPUESTA:
        """
        
        # Aquí imprimiríamos el prompt para que el usuario lo vea
        return system_prompt

if __name__ == "__main__":
    try:
        rag = RAGSystem()
        rag.load_documents("./data")
        rag.chunk_documents()
        rag.build_index()
        
        if rag.index is None:
            print("El sistema no pudo iniciarse correctamente.")
        else:
            print("\n--- SISTEMA LISTO ---")
            while True:
                user_query = input("\nPregunta (o escribe 'salir'): ")
                if user_query.lower() == 'salir':
                    break
                    
                context = rag.retrieve(user_query)
                prompt_with_context = rag.generate_response(user_query, context)
                
                print("\n--- PROMPT GENERADO PARA EL LLM ---")
                print(prompt_with_context)
    except KeyboardInterrupt:
        print("\nPrograma detenido por el usuario.")
    except Exception as e:
        print(f"\nOcurrió un error inesperado: {e}")
