from fastapi import FastAPI

app = FastAPI(
    title="SecondCommit API",
    description="Backend API for the SecondCommit platform.",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "Welcome to SecondCommit API 🚀"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }