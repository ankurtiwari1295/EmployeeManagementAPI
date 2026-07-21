from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
)

import shutil
import uuid

from pathlib import Path

router = APIRouter(
    prefix="/files",
    tags=["Files"],
)

ALLOWED_TYPES = [
    "image/png",
    "image/jpeg",
]

UPLOAD_DIR = Path("uploads")

UPLOAD_DIR.mkdir(
    exist_ok=True,
)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
):

    # Validate file type.
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only PNG and JPEG files are allowed",
        )

    # Generate unique filename.
    filename = f"{uuid.uuid4()}_{file.filename}"

    file_path = UPLOAD_DIR / filename

    with open(
        file_path,
        "wb",
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer,
        )

    return {
        "filename": filename,
        "content_type": file.content_type,
    }
