#backend/main.py
import os
import json
import psutil
import platform
import GPUtil  # Only if you have a GPU and GPUtil installed
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import subprocess
import logging
import crud
import models
import schemas
from database import SessionLocal, engine

# Create the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def call_ollama_cli(model: str, prompt: str) -> str:
    command = ["ollama", "run", model, prompt]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error calling Ollama CLI: {e.stderr}")
        raise Exception(f"Ollama CLI error: {e.stderr}")

# ✅ Load reasoning templates ONCE at startup to avoid redundant file reads
def load_reasoning_templates():
    with open("reasoning_templates.json", "r") as file:
        return json.load(file)

reasoning_templates = load_reasoning_templates()  # Load once at startup

def auto_select_reasoning(question):
    if "why" in question.lower():
        return "explanatory"
    elif "compare" in question.lower() or "difference" in question.lower():
        return "comparative"
    elif "steps" in question.lower() or "process" in question.lower():
        return "step_by_step"
    elif "alternatives" in question.lower():
        return "alternatives"
    else:
        return "default"

def generate_reasoning_prompt(question, user_selected_reasoning=None):
    reasoning_style = user_selected_reasoning or auto_select_reasoning(question)
    template = reasoning_templates.get(reasoning_style, reasoning_templates["default"])
    return f"I want to understand how you arrive at your answer. {template} Question: {question}"

# ✅ Fix `call_ollama_with_reasoning` to properly support MULTIPLE models
def call_ollama_with_reasoning(model, question, reasoning_style=None):
    prompt = generate_reasoning_prompt(question, reasoning_style)

    command = ["ollama", "run", model, prompt]  # ✅ Ensure model is correctly passed
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error calling Ollama CLI: {e.stderr}")
        return "Error: Could not process your request."

def process_ollama_response(response):
    if "Final Answer:" in response:
        parts = response.split("Final Answer:")
        reasoning = parts[0].strip()
        answer = parts[1].strip()
    else:
        reasoning = response
        answer = "No explicit final answer found."
    return {"reasoning": reasoning, "answer": answer}

@app.post("/session", response_model=schemas.Session)
def create_new_session(db: Session = Depends(get_db)):
    """
    Create a new chat session.
    """
    session_obj = crud.create_session(db)
    return session_obj

@app.get("/models")
def get_installed_models():
    models_dir = os.path.expanduser("~/.ollama/models/manifests/registry.ollama.ai/library")
    
    try:
        if not os.path.exists(models_dir):
            raise HTTPException(status_code=500, detail="Models directory not found")

        model_list = []

        # Iterate through all directories in the models folder
        for model_folder in os.listdir(models_dir):
            model_path = os.path.join(models_dir, model_folder)
            
            # If it's a directory, check inside for submodels
            if os.path.isdir(model_path):
                sub_models = [
                    f"{model_folder}:{file}" for file in os.listdir(model_path)
                    if os.path.isfile(os.path.join(model_path, file))
                ]
                if sub_models:
                    model_list.extend(sub_models)
                else:
                    model_list.append(model_folder)  # If no files, just list the model name
        
        return {"models": model_list}
    
    except Exception as e:
        logging.error(f"Error retrieving models: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving installed models")
        
@app.post("/chat", response_model=schemas.ChatResponse)
def send_chat_message(chat_request: schemas.ChatRequest, db: Session = Depends(get_db)):
    """
    Receive a chat message, call the selected language model via the CLI,
    save both the user message and model response, and return the responses.
    """

    session_obj = crud.get_session(db, chat_request.session_id)
    if session_obj is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save the user's message
    crud.create_message(db, session_obj.id, sender="user", content=chat_request.message)

    # ✅ Ensure model selection works properly
    model = chat_request.model_id
    reasoning_style = chat_request.reasoning_style  
    ollama_response = call_ollama_with_reasoning(model, chat_request.message, reasoning_style)

    response_data = process_ollama_response(ollama_response)

    # Save model's response
    crud.create_message(db, session_obj.id, sender="model", content=response_data["answer"])

    return schemas.ChatResponse(
        session_id=session_obj.id,
        user_message=chat_request.message,
        model_message=response_data["answer"],
        model_reasoning=response_data["reasoning"],
        model_id=model,
    )

@app.get("/chat/{session_id}", response_model=schemas.Session)
def get_chat_history(session_id: int, db: Session = Depends(get_db)):
    """
    Retrieve the full chat history (i.e. all messages) for a given session.
    """
    session_obj = crud.get_session(db, session_id)
    if session_obj is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_obj

@app.get("/metrics")
def get_hardware_metrics():
    try:
        # CPU metrics
        cpu_usage = psutil.cpu_percent(interval=1)  # overall CPU percentage
        per_core_usage = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else None
        
        # Memory metrics
        virtual_mem = psutil.virtual_memory()
        memory_usage_percent = virtual_mem.percent
        memory_used = virtual_mem.used
        memory_total = virtual_mem.total

        # Disk I/O (you can expand this as needed)
        disk_io = psutil.disk_io_counters()
        disk_read = disk_io.read_bytes if disk_io else None
        disk_write = disk_io.write_bytes if disk_io else None

        # GPU metrics (if available)
        gpu_metrics = []
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                gpu_metrics.append({
                    "name": gpu.name,
                    "load": gpu.load * 100,  # as percent
                    "memoryUsed": gpu.memoryUsed,
                    "memoryTotal": gpu.memoryTotal,
                    "temperature": gpu.temperature,
                })
        except Exception as gpu_error:
            logging.warning(f"GPU metrics not available: {gpu_error}")

        # Equipment information
        system_info = {
            "cpu_model": platform.processor(),
            "machine": platform.machine(),
            "system": platform.system(),
            "platform": platform.platform(),
        }

        return {
            "cpu": {
                "usage_percent": cpu_usage,
                "per_core_usage": per_core_usage,
                "frequency": cpu_freq,
            },
            "memory": {
                "usage_percent": memory_usage_percent,
                "used": memory_used,
                "total": memory_total,
            },
            "disk": {
                "read_bytes": disk_read,
                "write_bytes": disk_write,
            },
            "gpu": gpu_metrics,
            "system_info": system_info,
        }
    except Exception as e:
        logging.error(f"Error collecting metrics: {e}")
        raise HTTPException(status_code=500, detail="Error collecting hardware metrics")