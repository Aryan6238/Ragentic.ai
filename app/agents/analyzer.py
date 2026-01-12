from app.core.llm import llm_client

class AnalyzerAgent:
    """
    Agent responsible for synthesizing raw context into insights.
    """
    
    SYSTEM_PROMPT = """
    SYSTEM: You are an expert Research Analyst. Your job is to provide clear, detailed, and easy-to-understand answers that help people learn and understand complex topics.
    
    IMPORTANT GUIDELINES:
    - Use simple, everyday language - explain things like you're talking to a smart friend, not using technical jargon
    - Be comprehensive: provide detailed explanations, examples, and context
    - Write 200-300 words minimum - give thorough, valuable information
    - If context is provided, use it extensively. If context is limited, use your knowledge to provide helpful information
    - Structure your answer: start with a clear answer, then explain details, give examples, and discuss implications
    - Make it interesting and engaging - help the reader understand why this matters
    - Use bullet points or short paragraphs for clarity
    - Always be accurate and factual
    
    Task: Write a comprehensive, detailed answer (200-300 words) that thoroughly addresses the question. Use simple language that anyone can understand.
    """

    async def analyze(self, sub_question: str, context_chunks: list[str]) -> str:
        """
        Synthesizes an answer from the retrieved chunks.
        """
        context_str = "\n\n".join([f"[Chunk {i+1}]: {chunk}" for i, chunk in enumerate(context_chunks)])
        
        user_prompt = f"""
        Research Question: {sub_question}
        
        Available Information:
        {context_str if context_str else "No specific documents found. Use your knowledge to provide a comprehensive answer."}
        
        INSTRUCTIONS:
        - Provide a detailed, comprehensive answer (200-300 words minimum)
        - Use simple, easy-to-understand language
        - Explain concepts clearly - avoid jargon
        - Include examples and practical information
        - If you have context, use it extensively. If not, provide valuable information from your knowledge
        - Make it informative and helpful
        - Structure your answer clearly with good flow
        
        Write your comprehensive answer now:
        """
        
        response = await llm_client.generate_text(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt
        )
        
        return response.strip()

# Singleton
analyzer = AnalyzerAgent()
