# backend/api/models_list.py
from fastapi import APIRouter, HTTPException
import os
import logging

router = APIRouter()

@router.get("/models")
def get_installed_models():
    models_dir = os.path.expanduser("~/.ollama/models/manifests/registry.ollama.ai/library")
    
    try:
        if not os.path.exists(models_dir):
            raise HTTPException(status_code=500, detail="Models directory not found")

        model_list = []

        for model_folder in os.listdir(models_dir):
            model_path = os.path.join(models_dir, model_folder)
            
            if os.path.isdir(model_path):
                sub_models = [
                    f"{model_folder}:{file}" for file in os.listdir(model_path)
                    if os.path.isfile(os.path.join(model_path, file))
                ]
                if sub_models:
                    model_list.extend(sub_models)
                else:
                    model_list.append(model_folder)
        
        return {"models": model_list}
    
    except Exception as e:
        logging.error(f"Error retrieving models: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving installed models")