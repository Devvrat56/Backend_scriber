import os
import uuid
import json
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from db.session import get_db
from db import models
from services.scribe_service import scribe_service
from services.summary_service import summary_service
from core.config import settings
from pydantic import BaseModel
from typing import List, Dict

router = APIRouter(prefix="/scribe", tags=["AI Scribe"])

# Ensure the upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

class AnalysisRequest(BaseModel):
    transcript: str

class ScribeResult(BaseModel):
    transcript: str
    entities: List[Dict]
    summary: str

class PDFRequest(BaseModel):
    transcript: str
    entities: List[Dict]
    summary_text: str

@router.post("/transcribe", response_model=Dict)
async def transcribe_audio(file: UploadFile = File(...)):
    # ... (existing allowed_extensions logic)
    allowed_extensions = {".wav", ".mp3", ".m4a", ".webm", ".mpga", ".mp4", ".mpeg", ".ogg"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported format: {file_ext}. Supported: {', '.join(sorted(allowed_extensions))}"
        )
    
    file_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    try:
        transcript = scribe_service.transcribe(file_path)
        os.remove(file_path)
        return {"transcript": transcript}
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze", response_model=ScribeResult)
async def analyze_transcript(request: AnalysisRequest, db: Session = Depends(get_db)):
    try:
        entities = scribe_service.extract_entities(request.transcript)
        summary = summary_service.generate_clinical_summary(request.transcript, entities)
        
        # Persistence Logic
        session = models.ScribeSession(
            transcript=request.transcript,
            summary=summary,
            entities=json.dumps(entities)
        )
        db.add(session)
        db.commit()
        
        return {
            "transcript": request.transcript,
            "entities": entities,
            "summary": summary
        }
    except Exception as e:
        db.rollback()
        print(f"Scribe Analysis Failed: {str(e)}") # Critical for backend visibility
        raise HTTPException(status_code=500, detail=f"Analysis Engine Error: {str(e)}")

@router.post("/summarize")
async def generate_summary_only(request: AnalysisRequest):
    try:
        entities = scribe_service.extract_entities(request.transcript)
        summary = summary_service.generate_clinical_summary(request.transcript, entities)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-pdf")
async def generate_pdf(request: PDFRequest):
    try:
        file_id = str(uuid.uuid4())
        pdf_filename = f"Summary_{file_id}.pdf"
        file_path = os.path.join(settings.UPLOAD_DIR, pdf_filename)
        
        summary_service.generate_pdf_summary(
            transcript=request.transcript,
            entities=request.entities,
            summary_text=request.summary_text,
            output_path=file_path
        )
        
        return FileResponse(
            path=file_path,
            filename=pdf_filename,
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
