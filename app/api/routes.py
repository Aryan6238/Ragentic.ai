from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form
from app.api.models import (
    ResearchRequest, ResearchResponse, StreamLog, FinalReportRepsonse,
    DocumentUploadResponse, DocumentQnARequest, DocumentQnAResponse
)
import uuid
from typing import Dict, List, Optional

router = APIRouter()

# In-memory store for task status (replace with proper DB/Redis in prod)
# task_id -> List[StreamLog]
task_logs: Dict[str, List[StreamLog]] = {}
# task_id -> FinalReportRepsonse
task_results: Dict[str, FinalReportRepsonse] = {}

from app.agents.orchestrator import orchestrator
from app.services.document_manager import document_manager
from app.core.llm import llm_client

async def run_agent_workflow(task_id: str, topic: str):
    """
    Wrapper to run the orchestrator and handle result storage.
    """
    async def log_callback(t_id, status, details, step):
        task_logs[t_id].append(StreamLog(task_id=t_id, status=status, details=details, step=step))
    
    try:
        # Initial Log
        await log_callback(task_id, "Started", f"Researching: {topic}", "planning")
        
        # Run the Brain
        report_html = await orchestrator.run_workflow(task_id, topic, log_callback)
        
        # Store Result
        task_results[task_id] = FinalReportRepsonse(
            task_id=task_id,
            topic=topic,
            content_html=report_html
        )
        
        # Final Log
        await log_callback(task_id, "Completed", "Report ready.", "completed")
        
    except Exception as e:
        # Error logging handled inside orchestrator, but we ensure status is updated here too
        pass

@router.post("/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    task_logs[task_id] = []
    
    # Start the real agent in the background
    background_tasks.add_task(run_agent_workflow, task_id, request.topic)
    
    return ResearchResponse(task_id=task_id, message="Research started successfully.")

@router.get("/stream/{task_id}", response_model=List[StreamLog])
async def get_stream(task_id: str):
    if task_id not in task_logs:
        return [] # Or 404, but empty list is safer for polling
    return task_logs[task_id]

@router.get("/result/{task_id}", response_model=FinalReportRepsonse)
async def get_result(task_id: str):
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail="Result not ready or task not found")
    return task_results[task_id]

# Document Upload Endpoints
@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    Upload documents for a session. Creates a new session if session_id is not provided.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    try:
        session_id, uploaded_files = await document_manager.upload_documents(files, session_id)
        session_info = document_manager.get_session_info(session_id)
        
        return DocumentUploadResponse(
            session_id=session_id,
            message=f"Successfully uploaded {len(uploaded_files)} document(s)",
            files_uploaded=uploaded_files,
            total_documents=session_info["document_count"] if session_info else 0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/documents/qa", response_model=DocumentQnAResponse)
async def ask_question(request: DocumentQnARequest):
    """
    Ask a question about uploaded documents using RAG.
    """
    if not request.session_id or request.session_id not in document_manager.sessions:
        raise HTTPException(status_code=404, detail="Session not found. Please upload documents first.")
    
    try:
        # Search documents
        chunks, sources = await document_manager.search_documents(request.session_id, request.question, k=5)
        
        if not chunks:
            return DocumentQnAResponse(
                answer="I couldn't find relevant information in your uploaded documents to answer this question. Please make sure your documents contain relevant information.",
                sources=[]
            )
        
        # Create context
        context_str = "\n\n".join([f"[Document Excerpt {i+1}]: {chunk}" for i, chunk in enumerate(chunks)])
        
        # Generate answer using LLM
        system_prompt = """You are a helpful assistant that answers questions based on the provided document excerpts. 
        Use only the information from the documents. If the documents don't contain enough information, say so.
        Be concise and accurate."""
        
        user_prompt = f"""Question: {request.question}

Document Excerpts:
{context_str}

Answer the question based on the document excerpts above:"""
        
        answer = await llm_client.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        return DocumentQnAResponse(
            answer=answer.strip(),
            sources=list(set(sources))
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")

@router.get("/documents/session/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a document session."""
    info = document_manager.get_session_info(session_id)
    if not info:
        raise HTTPException(status_code=404, detail="Session not found")
    return info

@router.delete("/documents/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and all its documents.
    This removes all uploaded files, vector data, and session information.
    """
    success = document_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session and all documents deleted successfully", "session_id": session_id}
