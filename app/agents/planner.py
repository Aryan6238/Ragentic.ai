import json
from typing import List
from datetime import datetime
from app.core.llm import llm_client

class PlannerAgent:
    """
    Agent responsible for breaking down a topic into sub-questions.
    """
    
    SYSTEM_PROMPT = """
    SYSTEM: You are an expert Research Planner. Your job is to break down complex topics into clear, comprehensive research questions that will help create a detailed and useful report.
    
    IMPORTANT GUIDELINES:
    - Create 5-7 well-thought-out sub-questions that cover different aspects of the topic
    - Questions should be specific, clear, and easy to understand
    - Cover: basics/overview, current state, challenges, opportunities, future trends, practical applications, and real-world impact
    - Use simple, everyday language - avoid jargon unless necessary
    - Make sure questions will lead to comprehensive, valuable information
    
    Task: Create a research plan with 5-7 distinct, comprehensive sub-questions.
    Format: JSON Array of strings. STRICTLY return ONLY the JSON array. No markdown, no explanations.
    Example: ["What is X and why does it matter?", "What is the current state of X today?", "What are the main challenges facing X?", "What opportunities does X present?", "What does the future look like for X?", "How is X being used in real-world applications?"]
    """

    async def plan(self, topic: str) -> List[str]:
        """
        Generates a list of sub-questions for the given topic.
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        user_prompt = f"""
        Research Topic: {topic}
        Current Date: {date_str}
        
        Create a comprehensive research plan that will help us write a detailed, valuable report.
        Think about what someone would want to know about this topic:
        - What is it? (basics and overview)
        - What's happening now? (current state)
        - What are the challenges? (problems and obstacles)
        - What are the opportunities? (potential and benefits)
        - What's coming next? (future trends and predictions)
        - How is it used? (practical applications)
        - Why does it matter? (real-world impact)
        
        Generate 5-7 comprehensive research questions (JSON array only):
        """
        
        response_text = await llm_client.generate_text(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt
        )
        
        # Clean the response to ensure valid JSON
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        
        try:
            plan = json.loads(clean_text)
            if not isinstance(plan, list):
                # Fallback if LLM returns bad structure
                return [f"Research {topic}"]
            return plan
        except json.JSONDecodeError:
            # Fallback if LLM failed JSON completely
            return [f"General research on {topic} (JSON Error)"]

# Singleton
planner = PlannerAgent()
