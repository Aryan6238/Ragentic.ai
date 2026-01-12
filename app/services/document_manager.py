import os
import uuid
import logging
from typing import Dict, List, Optional
from fastapi import UploadFile
import google.generativeai as genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np

from app.core.config import settings
from app.services.vector_db import vector_db

logger = logging.getLogger("uvicorn")

class DocumentManager:
    """
    Manages user-uploaded documents with session-based isolation.
    Each session has its own vector store.
    """
    
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Session storage: session_id -> {vector_db, documents}
        self.sessions: Dict[str, Dict] = {}
        
        # Ensure upload directory exists
        self.upload_dir = os.path.join(settings.DATA_DIR, "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def _create_session_vector_db(self, session_id: str):
        """Create a new vector database for a session."""
        # Replacing FAISS with simple in-memory list for transient session storage
        return {"vectors": [], "metadata": []}
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using Gemini."""
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return []
    
    def _get_query_embedding(self, text: str) -> List[float]:
        """Get query embedding."""
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            return []
    
    async def upload_documents(self, files: List[UploadFile], session_id: Optional[str] = None) -> tuple[str, List[str]]:
        """
        Upload and process documents for a session.
        Returns (session_id, list of uploaded filenames)
        """
        # Create or get session
        if not session_id or session_id not in self.sessions:
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = {
                "vector_db": self._create_session_vector_db(session_id),
                "documents": []
            }
        
        session = self.sessions[session_id]
        uploaded_files = []
        
        # Process each file
        for file in files:
            try:
                # Validate file type
                if not file.filename:
                    continue
                    
                ext = os.path.splitext(file.filename)[1].lower()
                if ext not in ['.txt', '.md', '.pdf']:
                    logger.warning(f"Unsupported file type: {ext}")
                    continue
                
                # Save file
                file_path = os.path.join(self.upload_dir, f"{session_id}_{file.filename}")
                content = await file.read()
                
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                # Read text content
                if ext == '.pdf':
                    # Try to extract text from PDF
                    try:
                        text = content.decode('utf-8', errors='ignore')
                        # If it's binary PDF, we'll get mostly garbage, but some text might be readable
                        if len(text.strip()) < 100:  # Likely binary PDF
                            text = f"[PDF file: {file.filename} - Text extraction limited. For better results, convert to TXT first.]"
                    except Exception as e:
                        logger.warning(f"PDF reading issue for {file.filename}: {e}")
                        text = f"[PDF file: {file.filename} - Could not extract text. Please convert to TXT format for best results.]"
                else:
                    text = content.decode('utf-8', errors='ignore')
                
                # Process document
                chunks = self.text_splitter.split_text(text)
                
                # Create embeddings and add to session vector DB
                vectors_to_add = []
                metadata_to_add = []
                
                for chunk in chunks:
                    embedding = self._get_embedding(chunk)
                    if embedding:
                        vectors_to_add.append(embedding)
                        metadata_to_add.append({
                            "text": chunk,
                            "source": file.filename
                        })
                
                # Add to session vector DB
                if vectors_to_add:
                    vdb = session["vector_db"]
                    vdb["vectors"].extend(vectors_to_add)
                    vdb["metadata"].extend(metadata_to_add)
                
                session["documents"].append(file.filename)
                uploaded_files.append(file.filename)
                
                logger.info(f"Processed {file.filename}: {len(chunks)} chunks, {len(vectors_to_add)} vectors")
                
            except Exception as e:
                logger.error(f"Error processing {file.filename}: {e}")
                continue
        
        return session_id, uploaded_files
    
    async def search_documents(self, session_id: str, query: str, k: int = 5) -> tuple[List[str], List[str]]:
        """
        Search documents in a session.
        Returns (list of text chunks, list of source filenames)
        """
        if session_id not in self.sessions:
            return [], []
        
        session = self.sessions[session_id]
        vdb = session["vector_db"]
        
        vectors = vdb["vectors"]
        if not vectors:
            return [], []
        
        # Get query embedding
        query_vector = self._get_query_embedding(query)
        if not query_vector:
            return [], []
        
        # Simple Cosine Similarity using Numpy
        # 1. Convert to numpy arrays
        vecs = np.array(vectors)
        q = np.array(query_vector)
        
        # 2. Normalize (Gemini embeddings are usually normalized, but safe to do)
        vecs_norm = np.linalg.norm(vecs, axis=1)
        q_norm = np.linalg.norm(q)
        
        # Avoid division by zero
        vecs_norm[vecs_norm == 0] = 1e-10
        if q_norm == 0:
            q_norm = 1e-10
            
        # 3. Calculate Sim
        # Dot product
        dot_product = np.dot(vecs, q)
        # Cosine sim
        similarities = dot_product / (vecs_norm * q_norm)
        
        # 4. Get top k
        # argsort returns indices of sorted from low to high, so we reverse
        top_indices = np.argsort(similarities)[-k:][::-1]
        
        results = []
        sources = set()
        
        for idx in top_indices:
            # We must ensure we don't go out of bounds if k > len
            if idx < len(vdb["metadata"]):
                item = vdb["metadata"][idx]
                results.append(item["text"])
                sources.add(item["source"])
        
        return results, list(sources)
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get information about a session."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        return {
            "session_id": session_id,
            "document_count": len(session["documents"]),
            "documents": session["documents"],
            "vector_count": len(session["vector_db"]["vectors"])
        }
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its associated data.
        Returns True if deleted, False if session not found.
        """
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        # Delete uploaded files
        for filename in session["documents"]:
            file_path = os.path.join(self.upload_dir, f"{session_id}_{filename}")
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted file: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")
        
        # Remove session from memory
        del self.sessions[session_id]
        
        logger.info(f"Deleted session: {session_id}")
        return True

# Singleton
document_manager = DocumentManager()

