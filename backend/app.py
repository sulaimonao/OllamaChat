# backend/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import json # Import json module
import os

from database import engine
import models
from api import chat, session, models_list, chat_history, metrics, web_search, upload, custom_inference
from code_execution import executor

# --- Load System Prompts ---
SYSTEM_PROMPTS_FILE = os.path.join(os.path.dirname(__file__), "system_prompts.json")
try:
    with open(SYSTEM_PROMPTS_FILE, "r") as f:
        system_prompts = json.load(f)
except FileNotFoundError:
    logging.error(f"System prompts file not found: {SYSTEM_PROMPTS_FILE}")
    system_prompts = {"default": {"description": "Default Assistant", "prompt": "You are a helpful assistant."}}
except json.JSONDecodeError:
    logging.error(f"Error decoding JSON in system prompts file: {SYSTEM_PROMPTS_FILE}")
    system_prompts = {"default": {"description": "Default Assistant", "prompt": "You are a helpful assistant."}}

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