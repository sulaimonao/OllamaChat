# backend/app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import json
import os

from database import engine
import models
from api import chat, session, models_list, chat_history, metrics, web_search, upload, custom_inference
from code_execution import executor
from config import load_system_prompts  # Make sure this import is correct

# --- Load System Prompts ---
SYSTEM_PROMPTS_FILE = os.path.join(os.path.dirname(__file__), "system_prompts.json")  # This is probably NOT the correct path!
# Correct path
SYSTEM_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "system_prompts")

try:
    # Don't load a single file. Load the directory
    system_prompts = load_system_prompts(SYSTEM_PROMPTS_DIR) # Use load_system_prompts and the correct directory.
except FileNotFoundError:
    logging.error(f"System prompts directory not found: {SYSTEM_PROMPTS_DIR}")
    system_prompts = {"default": {"description": "Default Assistant", "prompt": "You are a helpful assistant."}}
except json.JSONDecodeError:  # This exception handling isn't needed anymore
    logging.error(f"Error decoding JSON in system prompts file: {SYSTEM_PROMPTS_DIR}")
    system_prompts = {"default": {"description": "Default Assistant", "prompt": "You are a helpful assistant."}}


# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or, better, restrict to your frontend origin: ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging configuration
logging.basicConfig(level=logging.INFO)

# Create the custom models directory.
os.makedirs(os.path.join(os.path.dirname(__file__), "installed_models"), exist_ok=True)
# Create system_prompts directory (This is redundant - it should be created by the project structure)
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

@app.get("/workspaces")
async def list_workspaces_endpoint():
    try:
        workspaces = []
        for item in os.listdir(executor.BASE_WORKSPACE_DIR):
            item_path = os.path.join(executor.BASE_WORKSPACE_DIR, item)
            if os.path.isdir(item_path):
                workspaces.append({"id": item, "name": item})
        return {"workspaces": workspaces}
    except Exception as e:
        logging.exception("Error listing workspaces")
        raise HTTPException(status_code=500, detail="Could not list workspaces")

@app.delete("/workspace/{workspace_id}")
async def delete_workspace_endpoint(workspace_id: str):
    executor.delete_workspace(workspace_id)
    return {"message": f"Workspace {workspace_id} deleted"}

@app.get("/system_prompts")
async def get_system_prompts_endpoint():
    descriptions = {key: value["description"] for key, value in system_prompts.items()}
    print("System prompt descriptions (backend):", descriptions)  # Keep this for now
    return {"system_prompts": descriptions}