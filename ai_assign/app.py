from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import json
import os

# Import the core agent logic
from agent import run_newsletter_agent

app = FastAPI(title="Newsletter Agent API")

# Ensure static directory exists
os.makedirs("static", exist_ok=True)

class GenerateRequest(BaseModel):
    goal: str

@app.post("/api/generate")
def generate_newsletter(req: GenerateRequest):
    try:
        # Run agent in fully autonomous mode
        html_output = run_newsletter_agent(goal=req.goal, autonomous=True)
        if not html_output:
            raise HTTPException(status_code=500, detail="Failed to generate newsletter.")
        return {"status": "success", "html": html_output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/archive")
def get_archive():
    archive_path = "memory/news_archive.json"
    if not os.path.exists(archive_path):
        return []
    try:
        with open(archive_path, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")

# Serve the static directory
app.mount("/", StaticFiles(directory="static"), name="static")
