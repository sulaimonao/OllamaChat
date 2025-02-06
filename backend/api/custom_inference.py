# backend/api/custom_inference.py
import os
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from transformers import PaliGemmaProcessor, PaliGemmaForConditionalGeneration
from PIL import Image
from typing import Optional, Dict, Any
import base64
import io
import torch

router = APIRouter()

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "installed_models")

# --- Model Loading and Management ---
loaded_models: Dict[str, Any] = {}

def load_model(model_name: str):
    model_path = os.path.join(MODELS_DIR, model_name)
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found in installed_models")

    try:
        processor = PaliGemmaProcessor.from_pretrained(model_path)
        # Force float32, remove torch_dtype and device_map
        model = PaliGemmaForConditionalGeneration.from_pretrained(
            model_path
        ).eval()
        if torch.backends.mps.is_available():
            model = model.to("mps")
        loaded_models[model_name] = (model, processor)
        logging.info(f"Loaded model '{model_name}'")
    except Exception as e:
        logging.error(f"Error loading model '{model_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load model '{model_name}'")

def get_model(model_name: str):
    if model_name not in loaded_models:
        load_model(model_name)
    return loaded_models[model_name]

# --- API Endpoints ---
class ChatRequest(BaseModel):
    prompt: Optional[str] = ""
    image: Optional[str] = None
    model: str

class ChatResponse(BaseModel):
    response: str

@router.post("/custom_chat", response_model=ChatResponse)
async def custom_chat(request: ChatRequest):
    try:
        model, processor = get_model(request.model)

        # --- Handle Image Input ---
        if request.image:
            try:
                image_bytes = base64.b64decode(request.image)
                image = Image.open(BytesIO(image_bytes))
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid image data: {e}")
        else:
            image = None

        # --- Prepare Prompt ---
        prompt = request.prompt if request.prompt else ""

        # --- Tokenization and Processing ---
        if image:
            model_inputs = processor(text=prompt, images=image, return_tensors="pt")
        else:
            model_inputs = processor(text=prompt, return_tensors="pt")

        #Move to device
        model_inputs = model_inputs.to(model.device)

        input_len = model_inputs["input_ids"].shape[-1]

        # --- Inference ---
        with torch.inference_mode():
            generation = model.generate(**model_inputs, max_new_tokens=100, do_sample=False)
            generation = generation[0][input_len:]
            response_text = processor.decode(generation, skip_special_tokens=True)

        return ChatResponse(response=response_text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/custom_models")
async def list_custom_models():
    try:
        return {"models": os.listdir(MODELS_DIR)}
    except Exception as e:
        logging.error("Could not find list of custom models.")
        raise HTTPException(status_code=500, detail=str(e))