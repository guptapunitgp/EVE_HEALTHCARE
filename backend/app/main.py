from fastapi import FastAPI

app = FastAPI(
    title="EVE Healthcare API",
    description="Diagnostic test booking and simulated payment API",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "success": True,
        "message": "EVE Healthcare API is running",
    }


@app.get("/health")
def health_check():
    return {
        "success": True,
        "status": "healthy",
    }