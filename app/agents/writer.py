from typing import List
from app.core.llm import llm_client

class WriterAgent:
    """
    Agent responsible for compiling the final report in HTML.
    """
    
    SYSTEM_PROMPT = """
    SYSTEM: You are a world-class Research Report Writer. Your job is to create comprehensive, detailed, and easy-to-understand research reports that are valuable and engaging for readers.
    
    CRITICAL REQUIREMENTS:
    - Write in SIMPLE, CLEAR language - use everyday words, avoid complex jargon
    - Be COMPREHENSIVE: create a detailed report (minimum 2000 words total)
    - Structure: Executive Summary, Detailed Sections, Key Takeaways, Conclusion
    - Each section should be thorough (300-500 words per section)
    - Use real examples and practical applications
    - Explain concepts clearly - assume the reader is smart but not an expert
    - Make it engaging and interesting to read
    
    HTML FORMATTING REQUIREMENTS:
    - Use <h1> for the main title
    - Use <h2> for major section headers
    - Use <h3> for subsections
    - Use <p> for paragraphs (make them detailed, 4-6 sentences each)
    - Use <ul> and <ol> for lists
    - Use <blockquote> for important insights and key takeaways
    - Use <strong> for emphasis (wrap important terms)
    - Use <em> for subtle emphasis
    - Do NOT use markdown (no **bold**, no # headers). ONLY HTML tags.
    
    CONTENT REQUIREMENTS:
    - Start with an Executive Summary (overview of the entire report)
    - Each section should have: introduction, detailed explanation, examples, implications
    - Include practical applications and real-world examples
    - Add a "Key Takeaways" section at the end
    - End with a comprehensive conclusion
    
    TONE: Professional but friendly, clear and accessible, engaging and informative. Write like you're explaining to an interested colleague who wants to learn.
    
    The output should be the raw HTML body content (no <html> or <body> tags needed, just the content).
    """

    async def write_report(self, topic: str, insights: List[str]) -> str:
        """
        Generates the final HTML report.
        """
        insights_str = "\n\n".join([f"Research Finding {i+1}:\n{insight}\n" for i, insight in enumerate(insights)])
        
        user_prompt = f"""
        Research Topic: {topic}
        
        DETAILED RESEARCH FINDINGS FROM OUR ANALYSIS:
        {insights_str}
        
        INSTRUCTIONS:
        1. Create a comprehensive, detailed research report on "{topic}"
        2. Use ALL the research findings provided above - expand on each one
        3. Write in simple, clear language that anyone can understand
        4. Make it comprehensive - aim for 2000+ words total
        5. Include:
           - Executive Summary (overview of the topic and key findings)
           - Detailed sections for each major aspect (use the research findings)
           - Real-world examples and practical applications
           - Key Takeaways section
           - Comprehensive Conclusion
        
        6. Use easy words - explain complex concepts simply
        7. Make it engaging and valuable - readers should learn something useful
        8. Structure it professionally with proper HTML headings and sections
        
        Write the complete, detailed HTML report now:
        """
        
        response = await llm_client.generate_text(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt
        )
        
        # Cleanup: sometimes LLMs wrap code in markdown blocks
        clean_html = response.replace("```html", "").replace("```", "").strip()
        
        return clean_html

# Singleton
writer = WriterAgent()
