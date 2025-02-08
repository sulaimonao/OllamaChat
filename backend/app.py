# backend/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from database import engine
import models
from api import chat, session, models_list, chat_history, metrics, web_search, upload, custom_inference
from code_execution import executor
from config import load_system_prompts  # Import the config loader

# --- Load System Prompts ---
SYSTEM_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "system_prompts")
system_prompts = load_system_prompts(SYSTEM_PROMPTS_DIR)

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

# Logging configuration
logging.basicConfig(level=logging.INFO)
# Create the custom models directory.
os.makedirs(os.path.join(os.path.dirname(__file__), "installed_models"), exist_ok=True)

# Create system_prompts directory.
os.makedirs(os.path.join(os.path.dirname(__file__), "system_prompts"), exist_ok=True)

# Include API routers
app.include_router(custom_inference.router)
app.include_router(chat.router)
app.include_router(session.router)
app.include_router(models_list.router)
app.include_router(chat_history.router)
app.include_router(metrics.router)
app.include_router(web_search.router)
app.include_router(upload.router)


# --- Workspace Management Endpoints ---
@app.post("/workspace/create")
async def create_workspace_endpoint():
    workspace_id, _ = executor.create_workspace()
    return {"workspace_id": workspace_id}

@app.get("/system_prompts")
async def get_system_prompts_endpoint():
    descriptions = {key: value["description"] for key, value in system_prompts.items()}
    return {"system_prompts": descriptions}