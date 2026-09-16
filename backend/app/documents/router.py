from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth import get_current_user_id
from app.database import get_db
from app.documents.schemas import DocumentResponse
from app.documents.services import process_and_save_document

router = APIRouter()


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document (PDF or TXT)",
    description="Uploads a PDF or TXT document, validates size & magic bytes, stores it in Supabase Storage, and creates a document record with status pending.",
)
async def upload_document(
    file: UploadFile = File(...),
    workspace_id: Optional[str] = Form(None),
    folder_id: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "MISSING_FILENAME",
                    "message": "Uploaded file must have a filename.",
                }
            },
        )

    file_bytes = await file.read()

    doc = process_and_save_document(
        db=db,
        user_id=user_id,
        file_bytes=file_bytes,
        original_filename=file.filename,
        workspace_id=workspace_id,
        folder_id=folder_id,
    )

    return doc
