from typing import List
from app.services.rag import rag_service

class ResearchAgent:
    """
    Agent responsible for gathering information using the RAG Service.
    Unlike other agents, this relies more on deterministic retrieval tools than LLM reasoning.
    """
    
    async def research(self, sub_question: str) -> List[str]:
        """
        Retrieves relevant context chunks for a sub-question.
        """
        # Call the RAG service to search the vector DB
        chunks = await rag_service.search(query=sub_question, k=5)
        
        if not chunks:
            return ["No specific internal documents found for this sub-question."]
            
        return chunks

# Singleton
researcher = ResearchAgent()
