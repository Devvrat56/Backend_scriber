import os
import uuid
from typing import List, Dict, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Body, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db import models
from services.chat_service import chat_service
from services.ocr_service import ocr_service
from services.summary_service import summary_service
from core.config import settings
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["AI Chatbot"])

class ChatRequest(BaseModel):
    message: str
    history: List[Dict] = []
    user_type: str = "patient"
    cancer_type: str = "Not specified"
    cancer_stage: str = "Unknown"
    age: Optional[int] = None
    symptoms: Optional[str] = None
    session_id: Optional[str] = None

@router.post("/message")
async def send_message(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        # 1. AI Logic
        result = chat_service.handle_message(
            message=request.message,
            history=request.history,
            user_type=request.user_type,
            cancer_type=request.cancer_type,
            cancer_stage=request.cancer_stage,
            age=request.age,
            symptoms=request.symptoms
        )
        
        # 2. Persistence Logic
        sid = request.session_id or str(uuid.uuid4())
        
        # Ensure session exists
        session = db.query(models.ChatSession).filter(models.ChatSession.id == sid).first()
        if not session:
            session = models.ChatSession(
                id=sid,
                user_type=request.user_type,
                cancer_type=request.cancer_type,
                cancer_stage=request.cancer_stage
            )
            db.add(session)
            db.flush()
            
        # Add User Message
        db.add(models.ChatMessage(session_id=sid, role="user", content=request.message))
        # Add Assistant Message
        db.add(models.ChatMessage(session_id=sid, role="assistant", content=result.get("answer", "")))
        
        db.commit()
        
        # Return result with session_id so frontend can keep using it
        result["session_id"] = sid
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summarize")
async def summarize_chat(history: List[Dict] = Body(...)):
    try:
        summary = chat_service.summarize_conversation(history)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-report")
async def upload_report(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith((".pdf", ".png", ".jpg", ".jpeg")):
        raise HTTPException(status_code=400, detail="Unsupported file format.")
    
    file_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    try:
        # 1. Extract Text
        text = ocr_service.extract_text_from_file(file_path)
        
        # 2. AI Summarization
        summary = summary_service.summarize_report(text)
        
        # 3. Persistence Logic
        analysis = models.ReportAnalysis(
            file_name=file.filename,
            extracted_text=text,
            summary=summary
        )
        db.add(analysis)
        db.commit()
        
        os.remove(file_path)
        return {"extracted_text": text, "summary": summary}
    except Exception as e:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))
