import os
import uuid
from typing import List, Dict, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from services.chat_service import chat_service
from services.ocr_service import ocr_service
from core.config import settings
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["AI Chatbot"])

class ChatRequest(BaseModel):
    message: str
    history: List[Dict] = []
    user_type: str = "patient"
    cancer_type: str = "Not specified"
    cancer_stage: str = "Unknown"

@router.post("/message")
async def send_message(request: ChatRequest):
    try:
        result = chat_service.handle_message(
            message=request.message,
            history=request.history,
            user_type=request.user_type,
            cancer_type=request.cancer_type,
            cancer_stage=request.cancer_stage
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-report")
async def upload_report(file: UploadFile = File(...)):
    if not file.filename.endswith((".pdf", ".png", ".jpg", ".jpeg")):
        raise HTTPException(status_code=400, detail="Unsupported file format.")
    
    file_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    try:
        text = ocr_service.extract_text_from_file(file_path)
        os.remove(file_path)
        return {"extracted_text": text}
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))
