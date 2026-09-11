from fastapi import Depends, FastAPI

from app.auth import get_current_user_id

app = FastAPI(title="Personal Knowledge Assistant API")


@app.get("/")
def read_root():
    return {"message": "Welcome to Personal Knowledge Assistant API"}


@app.get("/api/v1/users/me")
def get_me(user_id: str = Depends(get_current_user_id)):
    return {"user_id": user_id, "status": "authenticated"}
