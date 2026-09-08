from fastapi import FastAPI

app = FastAPI(title="Personal Knowledge Assistant API")

@app.get("/")
def read_root():
    return {"message": "Welcome to Personal Knowledge Assistant API"}
