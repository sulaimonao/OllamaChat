# backend/api/session.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

import crud
import schemas

router = APIRouter()

@router.post("/session", response_model=schemas.Session)
def create_new_session(db: Session = Depends(crud.get_db)):
    try:
        session_obj = crud.create_session(db)
        return session_obj
    except Exception as e:
        logging.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail="Error creating session")