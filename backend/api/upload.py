# backend/api/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from utils import upload_file_to_dir  # Import from utils

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    return upload_file_to_dir(file)  # Use the utility function