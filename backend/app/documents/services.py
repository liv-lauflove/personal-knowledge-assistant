import re
import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Document, DocumentStatus, User, Workspace
from app.storage import upload_file

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

# Common binary magic headers that must not be treated as text
BINARY_SIGNATURES = [
    b"\x89PNG\r\n\x1a\n",  # PNG
    b"\xff\xd8\xff",  # JPEG
    b"GIF87a",  # GIF
    b"GIF89a",  # GIF
    b"PK\x03\x04",  # ZIP, DOCX, XLSX, etc.
    b"MZ",  # Windows PE executable
    b"\x7fELF",  # Linux ELF executable
    b"\x1f\x8b",  # GZIP
    b"\x42\x5a\x68",  # BZIP2
    b"\xfd7zXZ\x00",  # XZ
    b"Rar!\x1a\x07",  # RAR
]


def validate_file_content(content: bytes, filename: str) -> str:
    """
    Validates file content using magic bytes and returns the detected MIME type.
    Supports only PDF and TXT files.
    """
    if not content:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {"code": "EMPTY_FILE", "message": "File cannot be empty."}
            },
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": f"File size exceeds the maximum allowed limit of {MAX_FILE_SIZE // (1024 * 1024)}MB.",
                }
            },
        )

    # 1. Check for PDF magic bytes (%PDF-)
    if content.startswith(b"%PDF-"):
        return "application/pdf"

    # 2. Check if content starts with known binary magic signatures
    for sig in BINARY_SIGNATURES:
        if content.startswith(sig):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_FILE_TYPE",
                        "message": "Binary file format detected. Only PDF and TXT files are supported.",
                    }
                },
            )

    # 3. Check for plain text (TXT)
    # Binary files typically contain null bytes in the header
    sample = content[:4096]
    if b"\x00" in sample:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_FILE_TYPE",
                    "message": "File content contains null bytes and is not valid plain text.",
                }
            },
        )

    # Ensure the content can be decoded as UTF-8
    try:
        content.decode("utf-8")
        return "text/plain"
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "UNSUPPORTED_ENCODING",
                    "message": "Plain text file must be valid UTF-8 encoded text.",
                }
            },
        )


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes filename to prevent directory traversal and special character issues.
    """
    filename = filename.replace("\\", "/").split("/")[-1]
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
    return safe_name or "uploaded_file"


def get_or_create_default_workspace(db: Session, user_id: str) -> Workspace:
    """
    Retrieves or creates a default workspace for the user.
    Ensures User record exists in DB if session user is new.
    """
    # Ensure user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user_name = user_id.split("@")[0] if "@" in user_id else "User"
        user_email = user_id if "@" in user_id else f"{user_id}@local.user"
        # Check if email is already taken
        existing_email_user = db.query(User).filter(User.email == user_email).first()
        if existing_email_user:
            user = existing_email_user
        else:
            user = User(id=user_id, name=user_name, email=user_email)
            db.add(user)
            db.commit()
            db.refresh(user)

    # Find existing workspace for this user
    workspace = (
        db.query(Workspace)
        .filter(Workspace.user_id == user.id)
        .order_by(Workspace.created_at.asc())
        .first()
    )
    if not workspace:
        workspace = Workspace(name="Default Workspace", user_id=user.id)
        db.add(workspace)
        db.commit()
        db.refresh(workspace)

    return workspace


def process_and_save_document(
    db: Session,
    user_id: str,
    file_bytes: bytes,
    original_filename: str,
    workspace_id: Optional[str] = None,
    folder_id: Optional[str] = None,
) -> Document:
    """
    Validates, uploads to Supabase Storage, and persists a Document record with status PENDING.
    """
    # 1. Validate content and detect MIME type
    mime_type = validate_file_content(file_bytes, original_filename)

    # 2. Resolve workspace with row-level ownership check
    if workspace_id:
        workspace = (
            db.query(Workspace)
            .filter(Workspace.id == workspace_id, Workspace.user_id == user_id)
            .first()
        )
        if not workspace:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "WORKSPACE_NOT_FOUND",
                        "message": "Workspace not found or access denied.",
                    }
                },
            )
    else:
        workspace = get_or_create_default_workspace(db, user_id)

    # 3. Generate document metadata
    doc_id = str(uuid.uuid4())
    safe_name = sanitize_filename(original_filename)
    storage_path = f"{workspace.id}/{doc_id}_{safe_name}"

    # 4. Upload to Supabase Storage
    upload_file(file_path=storage_path, file_bytes=file_bytes, content_type=mime_type)

    # 5. Save record to PostgreSQL database
    doc = Document(
        id=doc_id,
        workspace_id=workspace.id,
        folder_id=folder_id,
        title=original_filename,
        file_url=storage_path,
        file_size=len(file_bytes),
        mime_type=mime_type,
        status=DocumentStatus.PENDING,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return doc
