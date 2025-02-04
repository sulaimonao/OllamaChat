# backend/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from database import engine
import models
from api import chat, session, models_list, chat_history, metrics, web_search, upload

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging configuration (move to utils.py if you prefer)
logging.basicConfig(level=logging.INFO)

# Include API routers
app.include_router(chat.router)
app.include_router(session.router)
app.include_router(models_list.router)
app.include_router(chat_history.router)
app.include_router(metrics.router)
app.include_router(web_search.router)
app.include_router(upload.router)