from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Video Cutter Task Manager")

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/tasks")
def list_tasks():
    return []

@app.get("/api/downloads")
def list_downloads():
    return []

@app.get("/api/clips")
def list_clips():
    return []

@app.get("/api/upscale/tasks")
def list_upscale_tasks():
    return []

@app.get("/api/upscale/status")
def get_upscale_status():
    return {"state": "running"}

print("✅ Minimal FastAPI app created")
