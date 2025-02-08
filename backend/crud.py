#backend/crud.py
from sqlalchemy.orm import Session
import models
from database import SessionLocal, engine
from code_execution.executor import create_workspace # Import

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_session(db: Session):
    workspace_id, _ = create_workspace() # Create workspace
    db_session = models.ChatSession(workspace_id=workspace_id) # Assign to session
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_session(db: Session, session_id: int):
    return db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()

def create_message(db: Session, session_id: int, sender: str, content: str):
    db_message = models.Message(session_id=session_id, sender=sender, content=content)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_messages(db: Session, session_id: int):
    return db.query(models.Message).filter(models.Message.session_id == session_id).order_by(models.Message.timestamp).all()