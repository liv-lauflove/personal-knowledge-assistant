from fastapi import Depends, FastAPI

from app.auth import get_current_user_id
from app.documents import documents_router

app = FastAPI(title="Personal Knowledge Assistant API")

app.include_router(documents_router, prefix="/api/v1/documents", tags=["documents"])


@app.get("/")
def read_root():
    return {"message": "Welcome to Personal Knowledge Assistant API"}


@app.get("/api/v1/users/me")
def get_me(user_id: str = Depends(get_current_user_id)):
    return {"user_id": user_id, "status": "authenticated"}
