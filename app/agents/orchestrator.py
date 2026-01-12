import logging
import asyncio
from typing import Callable, Awaitable
from app.agents.planner import planner
from app.agents.researcher import researcher
from app.agents.analyzer import analyzer
from app.agents.writer import writer

logger = logging.getLogger("uvicorn")

class Orchestrator:
    """
    The conductor of the agent workflow.
    Manages the state and transition between agents.
    """
    
    async def run_workflow(self, task_id: str, topic: str, log_callback: Callable[[str, str, str], Awaitable[None]]):
        """
        Executes the full research workflow.
        
        Args:
            task_id: Unique ID for the job.
            topic: The user's query.
            log_callback: Async function to send logs back to the user (task_id, status, details).
        """
        try:
            # 1. PLANNING
            await log_callback(task_id, "Planning", "Analyzing topic and generating sub-questions...", "planning")
            plan = await planner.plan(topic)
            await log_callback(task_id, "Planning", f"Plan created with {len(plan)} steps.", "planning")
            
            insights = []
            
            # 2. EXECUTION LOOP
            for i, sub_question in enumerate(plan):
                step_log = f"Step {i+1}/{len(plan)}: {sub_question}"
                await log_callback(task_id, "Exec: Research", f"Searching documents for: {sub_question}", "researching")
                
                # A. Research (RAG)
                chunks = await researcher.research(sub_question)
                
                # B. Analyze (LLM)
                await log_callback(task_id, "Exec: Analyze", f"Synthesizing findings for: {sub_question}", "analyzing")
                insight = await analyzer.analyze(sub_question, chunks)
                insights.append(insight)
                
                # Small delay to prevent rate limits and give "vibe"
                await asyncio.sleep(0.5)

            # 3. WRITING
            await log_callback(task_id, "Writing", "Compiling final report...", "writing")
            final_report_html = await writer.write_report(topic, insights)
            
            return final_report_html

        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            await log_callback(task_id, "Error", f"Workflow aborted: {str(e)}", "error")
            raise e

# Singleton
orchestrator = Orchestrator()
