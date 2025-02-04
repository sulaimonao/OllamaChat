# backend/utils.py
import os
import shutil
import logging
from fastapi import UploadFile, HTTPException

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def upload_file_to_dir(file: UploadFile):  # Renamed to avoid conflict
    try:
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return {"filename": file.filename, "location": file_location}
    except Exception as e:
        logging.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")