import logging
from typing import Union
from supabase import create_client, Client
from app.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
BUCKET_NAME = "documents"

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
def upload_file(file_path: str, file_bytes: bytes, content_type: str) -> str:
    """
    Uploads a file to Supabase Storage and returns the path.
    Retries up to 3 times on failure with exponential backoff.
    """
    try:
        # Check if bucket exists, if not this will raise an exception (handled or ignored)
        res = supabase.storage.from_(BUCKET_NAME).upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": content_type}
        )
        return file_path
    except Exception as e:
        logger.error(f"Failed to upload file {file_path} to Supabase: {e}")
        raise e

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
def get_signed_url(file_path: str, expires_in: int = 3600) -> str:
    """
    Generates a signed URL for accessing a private file.
    Valid for `expires_in` seconds (default 1 hour).
    Retries up to 3 times on failure.
    """
    try:
        res = supabase.storage.from_(BUCKET_NAME).create_signed_url(
            path=file_path,
            expires_in=expires_in
        )
        
        # Depending on the supabase-python version, it returns a dict or string
        if isinstance(res, dict):
            return res.get("signedURL") or res.get("signedUrl")
        return str(res)
    except Exception as e:
        logger.error(f"Failed to generate signed URL for {file_path}: {e}")
        raise e
