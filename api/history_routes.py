from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from db.session import get_db
from db import models
import json

router = APIRouter(prefix="/history", tags=["Clinical History"])

@router.get("/all", response_model=Dict[str, List[Dict[str, Any]]])
async def get_all_history(db: Session = Depends(get_db)):
    try:
        # 1. Fetch Chat History
        chats = db.query(models.ChatSession).order_by(models.ChatSession.created_at.desc()).all()
        chat_list = []
        for c in chats:
            # Get the first message as a preview
            first_msg = db.query(models.ChatMessage).filter(models.ChatMessage.session_id == c.id).first()
            chat_list.append({
                "id": c.id,
                "type": "chat",
                "user_type": c.user_type,
                "cancer_type": c.cancer_type,
                "preview": first_msg.content if first_msg else "Empty conversation",
                "created_at": c.created_at
            })

        # 2. Fetch Scribe History
        scribes = db.query(models.ScribeSession).order_by(models.ScribeSession.created_at.desc()).all()
        scribe_list = []
        for s in scribes:
            scribe_list.append({
                "id": s.id,
                "type": "scribe",
                "transcript": s.transcript,
                "summary": s.summary,
                "entities": json.loads(s.entities) if s.entities else [],
                "created_at": s.created_at
            })

        # 3. Fetch Report History
        reports = db.query(models.ReportAnalysis).order_by(models.ReportAnalysis.created_at.desc()).all()
        report_list = []
        for r in reports:
            report_list.append({
                "id": r.id,
                "type": "report",
                "file_name": r.file_name,
                "extracted_text": r.extracted_text,
                "summary": r.summary if r.summary else "Summary pending redeployment.",
                "created_at": r.created_at
            })

        return {
            "chats": chat_list,
            "scribes": scribe_list,
            "reports": report_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
