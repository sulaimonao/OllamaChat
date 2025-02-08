# backend/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from database import engine
import models
from api import chat, session, models_list, chat_history, metrics, web_search, upload, custom_inference
from code_execution import executor  # Import the executor

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


# --- Code Execution Endpoints ---
@app.post("/execute")
async def execute(code: str, language: str, workspace_id: str):
    return executor.execute_code(code, language, workspace_id)

@app.post("/workspace/create")
async def create_workspace_endpoint():
    workspace_id, _ = executor.create_workspace()
    return {"workspace_id": workspace_id}

@app.delete("/workspace/{workspace_id}")
async def delete_workspace_endpoint(workspace_id: str):
    executor.delete_workspace(workspace_id)
    return {"message": f"Workspace {workspace_id} deleted"}

@app.get("/workspace/{workspace_id}/read")
async def read_file_endpoint(workspace_id: str, filename: str):
    return {"content": executor.read_file(workspace_id, filename)}

@app.post("/workspace/{workspace_id}/write")
async def write_file_endpoint(workspace_id: str, filename: str, content: str):
    executor.write_file(workspace_id, filename, content)
    return {"message": f"File '{filename}' written to workspace {workspace_id}"}