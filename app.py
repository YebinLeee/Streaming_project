import os
import asyncio
import signal
from fastapi import FastAPI, UploadFile, Form, HTTPException, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from typing import List, Optional, Dict, Any
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import shutil
import subprocess
from pathlib import Path
import aiofiles
import json
import uuid
import psutil
import atexit

# Ensure the services directory exists
os.makedirs(os.path.join(os.path.dirname(__file__), 'services'), exist_ok=True)

# Create FastAPI app
app = FastAPI(title="Video Streaming API")

# Create necessary directories
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "static/output"
RTSP_PORT = 8554  # Default RTSP port
Path(UPLOAD_DIR).mkdir(exist_ok=True)
Path(OUTPUT_DIR).mkdir(exist_ok=True, parents=True)

# Store RTSP server processes
rtsp_servers: Dict[str, Any] = {}

# Store RTSP server processes
rtsp_servers = {}

# Cleanup function to stop all RTSP servers on exit
def cleanup():
    from services.video_converter import rtsp_servers as rtsp_servers_dict
    for stream_id, process in list(rtsp_servers_dict.items()):
        try:
            if process and process.returncode is None:
                parent = psutil.Process(process.pid)
                for child in parent.children(recursive=True):
                    child.terminate()
                parent.terminate()
                process.wait()
        except Exception as e:
            print(f"Error stopping RTSP server {stream_id}: {e}")

# Register cleanup function
atexit.register(cleanup)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files with proper MIME types
class CustomStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if path.endswith('.m3u8'):
            response.headers['Content-Type'] = 'application/vnd.apple.mpegurl'
        elif path.endswith('.ts'):
            response.headers['Content-Type'] = 'video/MP2T'
        elif path.endswith('.mpd'):
            response.headers['Content-Type'] = 'application/dash+xml'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

app.mount("/static", CustomStaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Store chunk information for each task
chunk_storage = {}

# Store conversion tasks
conversion_tasks = {}

# Ensure upload directory exists
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "static/output"
Path(UPLOAD_DIR).mkdir(exist_ok=True)
Path(OUTPUT_DIR).mkdir(exist_ok=True, parents=True)

# Add health check endpoint
@app.get("/health", status_code=200)
async def health_check():
    return {"status": "healthy"}

# Import all route handlers
from routes.upload import router as upload_router
from routes.tasks import router as tasks_router
from routes.streaming import router as streaming_router

# Include all routers with their prefixes
app.include_router(upload_router, prefix="/api/v1", tags=["upload"])
app.include_router(tasks_router, prefix="/api/v1", tags=["tasks"])
app.include_router(streaming_router, prefix="/api/v1", tags=["streaming"])

# Add root endpoint
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
