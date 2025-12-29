import os
import faiss
import pickle
import numpy as np
from typing import List, Dict, Any
from app.core.config import settings
import logging

logger = logging.getLogger("uvicorn")

class VectorDB:
    """
    Wrapper around FAISS to handle vector storage and retrieval.
    Includes a metadata store (JSON/Pickle) to map vector IDs back to text.
    """
    
    def __init__(self):
        self.index_path = os.path.join(settings.DATA_DIR, "vector_store", "index.faiss")
        self.metadata_path = os.path.join(settings.DATA_DIR, "vector_store", "metadata.pkl")
        self.dimension = 768  # Dimension for Gemini Embeddings (text-embedding-004)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        self.index = self._load_index()
        self.metadata = self._load_metadata()

    def _load_index(self):
        if os.path.exists(self.index_path):
            return faiss.read_index(self.index_path)
        else:
            # Create a new FlatL2 index (Exact Search)
            return faiss.IndexFlatL2(self.dimension)

    def _load_metadata(self) -> Dict[int, Dict[str, Any]]:
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'rb') as f:
                return pickle.load(f)
        return {}

    def save(self):
        """Persist index and metadata to disk."""
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)

    def add_vectors(self, vectors: List[List[float]], metadatas: List[Dict[str, Any]]):
        """
        Add vectors and their metadata to the store.
        """
        if not vectors:
            return

        # Convert to float32 numpy array for FAISS
        vector_np = np.array(vectors).astype('float32')
        
        # Current index size is the starting ID for new vectors
        start_id = self.index.ntotal
        
        # Add to FAISS
        self.index.add(vector_np)
        
        # Add to Metadata store
        for i, meta in enumerate(metadatas):
            self.metadata[start_id + i] = meta
            
        self.save()
        logger.info(f"Added {len(vectors)} chunks to Vector DB.")

    def search(self, query_vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for top-k similar vectors.
        """
        if self.index.ntotal == 0:
            return []

        # FAISS search
        vector_np = np.array([query_vector]).astype('float32')
        distances, indices = self.index.search(vector_np, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx in self.metadata:
                item = self.metadata[idx]
                item['score'] = float(distances[0][i]) # L2 Distance (lower is better)
                results.append(item)
        
        return results

# Singleton
vector_db = VectorDB()
