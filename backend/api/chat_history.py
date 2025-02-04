# backend/api/chat_history.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud
import schemas

router = APIRouter()

@router.get("/chat/{session_id}", response_model=schemas.Session)
def get_chat_history(session_id: int, db: Session = Depends(crud.get_db)):
    try:
        session_obj = crud.get_session(db, session_id)
        if session_obj is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return session_obj
    except Exception as e:
        logging.error(f"Error retrieving chat history: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving chat history")