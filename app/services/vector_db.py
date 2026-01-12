import os
import pickle
import numpy as np
from typing import List, Dict, Any
from app.core.config import settings
import logging

from chromadb import Client
from chromadb.config import Settings

logger = logging.getLogger("uvicorn")


class VectorDB:
    """
    Wrapper around ChromaDB to handle vector storage and retrieval.
    Keeps the same public interface as the FAISS version.
    """

    def __init__(self):
        self.persist_dir = os.path.join(settings.DATA_DIR, "vector_store")
        self.dimension = 768  # Gemini embedding dimension

        os.makedirs(self.persist_dir, exist_ok=True)

        self.client = Client(
            Settings(
                persist_directory=self.persist_dir,
                anonymized_telemetry=False
            )
        )

        self.collection = self.client.get_or_create_collection(
            name="documents"
        )

    def save(self):
        """Persist ChromaDB state to disk."""
        self.client.persist()

    def add_vectors(self, vectors: List[List[float]], metadatas: List[Dict[str, Any]]):
        """
        Add vectors and metadata to ChromaDB.
        """
        if not vectors:
            return

        ids = [str(self.collection.count() + i) for i in range(len(vectors))]

        self.collection.add(
            embeddings=vectors,
            metadatas=metadatas,
            ids=ids
        )

        self.save()
        logger.info(f"Added {len(vectors)} chunks to Vector DB.")

    def search(self, query_vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for top-k similar vectors.
        """
        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=k
        )

        output = []
        for i in range(len(results["ids"][0])):
            item = results["metadatas"][0][i]
            item["score"] = float(results["distances"][0][i])  # lower = better
            output.append(item)

        return output


# Singleton
vector_db = VectorDB()
