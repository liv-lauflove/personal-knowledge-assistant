from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    folder_id: Optional[str] = None
    title: str
    file_url: str
    file_size: int
    mime_type: str
    status: str
    uploaded_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
