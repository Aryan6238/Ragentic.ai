import os
import glob
import logging
from typing import List, Dict, Any
import google.generativeai as genai
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.services.vector_db import vector_db

logger = logging.getLogger("uvicorn")

class RAGService:
    """
    Orchestrates:
    1. Reading files (Paper Fetching)
    2. Chunking
    3. Embedding (Via Gemini API)
    4. Storing in VectorDB
    5. Searching
    """
    
    def __init__(self):
        # Using Gemini for embeddings as per plan
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

    async def ingest_data_folder(self):
        """
        Reads all TXT/MD files from data/raw and indexes them.
        """
        raw_dir = os.path.join(settings.DATA_DIR, "raw")
        files = glob.glob(os.path.join(raw_dir, "**", "*.*"), recursive=True)
        
        documents = []
        for file_path in files:
            if file_path.endswith(('.txt', '.md', '.pdf')): # Basic support
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                        documents.append({"path": file_path, "text": text})
                except Exception as e:
                    logger.error(f"Failed to read {file_path}: {e}")

        if not documents:
            logger.info("No new documents found to ingest.")
            return

        # Processing documents
        vectors_to_add = []
        metadata_to_add = []

        for doc in documents:
            # 1. Chunking
            chunks = self.text_splitter.split_text(doc["text"])
            
            # 2. Embedding Batching (Gemini has limits, do small batches or one by one)
            # For simplicity in this demo, we do one by one or small groups.
            for chunk in chunks:
                embedding = self._get_embedding(chunk)
                if embedding:
                    vectors_to_add.append(embedding)
                    metadata_to_add.append({
                        "text": chunk,
                        "source": os.path.basename(doc["path"])
                    })
        
        # 3. Insertion
        if vectors_to_add:
            vector_db.add_vectors(vectors_to_add, metadata_to_add)

    def _get_embedding(self, text: str) -> List[float]:
        """
        Wraps Gemini Embedding API.
        """
        try:
            # 'models/text-embedding-004' is the current efficient model
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
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_query" # Important: different task type for queries
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            return []

    async def search(self, query: str, k: int=5) -> List[str]:
        """
        End-to-end retrieval.
        """
        # 1. Embed Query
        query_vector = self._get_query_embedding(query)
        if not query_vector:
            return []
            
        # 2. Vector Search
        results = vector_db.search(query_vector, k)
        
        # 3. Extract Text
        return [res["text"] for res in results]

rag_service = RAGService()
