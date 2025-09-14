# backend/tools/multimodal.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import uuid, os, json, datetime, yaml, hashlib
from typing import List, Optional, Dict, Any
from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
import paddleocr
from faster_whisper import WhisperModel
import subprocess
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
from scenedetect.scene_manager import save_images
from .search_engine import SearchEngine

# --- Pydantic Models ---
class ImageAnalysisResponse(BaseModel):
    captions: List[str]
    ocr: str
    objects: List[str]
    artifact_path: str

class AudioTranscriptionResponse(BaseModel):
    text: str
    segments: List[Dict[str, Any]]
    artifact_path: str

class VideoAnalysisResponse(BaseModel):
    summary: str
    frames: List[Dict[str, Any]]
    transcript: str
    artifact_path: str

class IngestPayload(BaseModel):
    modality: str
    metadata: Dict[str, Any]
    text: str
    fragments: List[Dict[str, Any]]

class IngestResponse(BaseModel):
    message: str
    ingested_file: str

# --- Router ---
router = APIRouter(prefix="/tools/mm", tags=["multimodal"])
MM_DIR = Path(__file__).resolve().parents[1] / "local_data" / "mm"
MM_DIR.mkdir(parents=True, exist_ok=True)

# --- Configuration ---
def get_config():
    here = Path(__file__).resolve()
    cfg_path = here.parents[1] / "config" / "mm.yaml"
    if cfg_path.exists():
        with cfg_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    import logging
    logging.getLogger(__name__).warning("mm.yaml not found; using empty config")
    return {}

config = get_config()
IMAGE_CONFIG = config.get("image", {})
AUDIO_CONFIG = config.get("audio", {})
VIDEO_CONFIG = config.get("video", {})

# --- Model Loading ---
blip_processor = None
blip_model = None
ocr_reader = None
asr_model = None

# Load BLIP model
try:
    model_name = IMAGE_CONFIG.get("caption_model", "blip-base")
    model_path = f"Salesforce/blip-image-captioning-{model_name}"
    blip_processor = BlipProcessor.from_pretrained(model_path)
    blip_model = BlipForConditionalGeneration.from_pretrained(model_path)
    print(f"BLIP model '{model_path}' loaded successfully.")
except Exception as e:
    blip_processor = None
    blip_model = None
    print(f"Warning: Could not load BLIP model: {e}")

# Load OCR model
if IMAGE_CONFIG.get("ocr") == "paddleocr":
    try:
        ocr_reader = paddleocr.PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        print("PaddleOCR model loaded successfully.")
    except Exception as e:
        ocr_reader = None
        print(f"Warning: Could not load PaddleOCR model: {e}")
elif IMAGE_CONFIG.get("ocr") == "tesseract":
    print("Tesseract OCR is configured but not implemented yet.")
    pass

# Load ASR model
try:
    model_name_from_config = AUDIO_CONFIG.get("asr_model", "faster-whisper-base")
    model_size = model_name_from_config.replace("faster-whisper-", "")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "int8" if device == "cpu" else "float16"

    asr_model = WhisperModel(model_size, device=device, compute_type=compute_type)
    print(f"Faster-Whisper model '{model_size}' loaded successfully on device '{device}'.")
except Exception as e:
    asr_model = None
    print(f"Warning: Could not load Faster-Whisper model: {e}")


def _save_temp(file: UploadFile, sub: str) -> Path:
    subdir = MM_DIR / "tmp" / sub
    subdir.mkdir(parents=True, exist_ok=True)
    p = subdir / f"{uuid.uuid4().hex}_{file.filename}"
    with p.open("wb") as f: f.write(file.file.read())
    return p

@router.get("/artifacts/{filepath:path}")
async def get_artifact(filepath: str):
    """Serves a previously generated multimodal artifact."""
    allowed_dir = MM_DIR.resolve()
    requested_path = (allowed_dir / filepath).resolve()

    if not requested_path.is_file() or not requested_path.is_relative_to(allowed_dir):
        raise HTTPException(status_code=404, detail="File not found or access denied")

    return FileResponse(str(requested_path))

@router.post("/image/analyze", response_model=ImageAnalysisResponse)
async def image_analyze(file: UploadFile = File(...)):
    p = _save_temp(file, "img")

    captions = []
    ocr_text = ""
    objects = []

    try:
        if blip_model and blip_processor:
            try:
                raw_image = Image.open(p).convert("RGB")
                inputs = blip_processor(raw_image, return_tensors="pt")
                out = blip_model.generate(**inputs)
                captions.append(blip_processor.decode(out[0], skip_special_tokens=True))
            except Exception as e:
                captions.append("Failed to generate caption.")
        else:
            captions.append("Captioning model not available.")

        if ocr_reader:
            try:
                result = ocr_reader.ocr(str(p), cls=True)
                if result and result[0] is not None:
                    ocr_text = "\n".join([line[1][0] for line in result[0]])
            except Exception as e:
                ocr_text = "Failed to perform OCR."
        else:
            ocr_text = "OCR not configured or failed to load."

        if IMAGE_CONFIG.get("detect_objects", False):
            objects.append("Object detection not implemented yet.")

    except Exception as e:
        captions.append("Failed to process image file.")
        ocr_text = "Failed to process image file."

    return ImageAnalysisResponse(
        captions=captions,
        ocr=ocr_text,
        objects=objects,
        artifact_path=str(p.relative_to(MM_DIR))
    )

@router.post("/audio/transcribe", response_model=AudioTranscriptionResponse)
async def audio_transcribe(file: UploadFile = File(...), lang: str | None = Form(None)):
    p = _save_temp(file, "aud")

    full_text = ""
    segments_data = []

    if asr_model:
        try:
            segments, info = asr_model.transcribe(str(p), language=lang, beam_size=5)
            all_text_parts = []
            for segment in segments:
                segments_data.append({"t0": segment.start, "t1": segment.end, "text": segment.text})
                all_text_parts.append(segment.text)
            full_text = "".join(all_text_parts).strip()
        except Exception as e:
            full_text = "Failed to transcribe audio."
    else:
        full_text = "ASR model not available."

    return AudioTranscriptionResponse(
        text=full_text,
        segments=segments_data,
        artifact_path=str(p.relative_to(MM_DIR))
    )

@router.post("/video/analyze", response_model=VideoAnalysisResponse)
async def video_analyze(file: UploadFile = File(...)):
    p = _save_temp(file, "vid")
    video_path_str = str(p)

    transcript = ""
    frames_data = []
    summary = ""

    video_artifacts_dir = p.parent / p.stem
    video_artifacts_dir.mkdir(exist_ok=True)

    try:
        audio_path = video_artifacts_dir / "audio.wav"
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", video_path_str, "-ac", "1", "-ar", "16000", "-vn", str(audio_path)],
                check=True, capture_output=True, timeout=120
            )
            if asr_model:
                segments, _ = asr_model.transcribe(str(audio_path))
                transcript = "".join([s.text for s in segments]).strip()
            else:
                transcript = "ASR model not available."
        except Exception:
            transcript = "Failed to extract or transcribe audio."

        try:
            video = open_video(video_path_str)
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector())
            scene_manager.detect_scenes(video=video, show_progress=False)
            scene_list = scene_manager.get_scene_list()

            if scene_list:
                image_filenames = save_images(
                    scene_list=scene_list, video=video, num_images=1,
                    output_dir=str(video_artifacts_dir), image_name_template='$SCENE_NUMBER'
                )
                for (scene_num, _), img_path in image_filenames.items():
                    scene = scene_list[scene_num - 1]
                    frame_info = {
                        "t": scene[1].get_seconds(),
                        "path": str(Path(img_path).relative_to(MM_DIR)),
                        "ocr": "", "caption": ""
                    }
                    if VIDEO_CONFIG.get("run_caption_on_keyframes", False) and blip_model:
                        raw_image = Image.open(img_path).convert("RGB")
                        inputs = blip_processor(raw_image, return_tensors="pt")
                        out = blip_model.generate(**inputs)
                        frame_info["caption"] = blip_processor.decode(out[0], skip_special_tokens=True)
                    if VIDEO_CONFIG.get("run_ocr_on_keyframes", False) and ocr_reader:
                        result = ocr_reader.ocr(img_path, cls=True)
                        if result and result[0] is not None:
                            frame_info["ocr"] = "\n".join([line[1][0] for line in result[0]])
                    frames_data.append(frame_info)
        except Exception:
            pass

        summary = " ".join([f["caption"] for f in frames_data if f["caption"]])

    except Exception as e:
        summary = f"A fatal error occurred during video analysis: {e}"

    return VideoAnalysisResponse(
        summary=summary, frames=frames_data, transcript=transcript,
        artifact_path=str(p.relative_to(MM_DIR))
    )

@router.post("/ingest", response_model=IngestResponse)
async def mm_ingest(payload: IngestPayload):
    data_dir = MM_DIR / payload.modality
    data_dir.mkdir(parents=True, exist_ok=True)
    original_file_path = payload.metadata.get("original_file", str(uuid.uuid4()))
    file_hash = hashlib.sha256(original_file_path.encode()).hexdigest()
    filepath = data_dir / f"{payload.modality}_{file_hash[:16]}.md"
    try:
        front_matter = {
            "source": "mm", "created_at": datetime.datetime.utcnow().isoformat(),
            **payload.metadata, "fragments": payload.fragments
        }
        content = f"---\n{yaml.dump(front_matter)}---\n\n{payload.text}"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        try:
            search_engine = SearchEngine()
            search_engine.index([str(filepath)])
            message = f"Successfully ingested and indexed {filepath}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to index document: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write ingest file: {e}")
    return IngestResponse(message=message, ingested_file=str(filepath))
