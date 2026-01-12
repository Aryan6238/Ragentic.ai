from pydantic import BaseModel
from typing import List, Optional

class ResearchRequest(BaseModel):
    topic: str
    
class ResearchResponse(BaseModel):
    task_id: str
    message: str

class StreamLog(BaseModel):
    task_id: str
    status: str
    details: Optional[str] = None
    step: str # "planning", "researching", "writing"

class FinalReportRepsonse(BaseModel):
    task_id: str
    topic: str
    content_html: str

# Document Upload Models
class DocumentUploadResponse(BaseModel):
    session_id: str
    message: str
    files_uploaded: List[str]
    total_documents: int

class DocumentQnARequest(BaseModel):
    session_id: str
    question: str

class DocumentQnAResponse(BaseModel):
    answer: str
    sources: List[str]  # Document names used