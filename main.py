import os
import asyncio
import signal
from fastapi import FastAPI, UploadFile, Form, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response
from typing import List, Optional
import os
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import aiofiles
import json
import uuid
import psutil
import atexit

app = FastAPI()

# Create necessary directories
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "static/output"
RTSP_PORT = 8554  # Default RTSP port
Path(UPLOAD_DIR).mkdir(exist_ok=True)
Path(OUTPUT_DIR).mkdir(exist_ok=True, parents=True)

# Store RTSP server processes
rtsp_servers: Dict[str, Any] = {}

# Cleanup function to stop all RTSP servers on exit
def cleanup():
    for stream_id, process in rtsp_servers.items():
        try:
            if process and process.poll() is None:
                parent = psutil.Process(process.pid)
                for child in parent.children(recursive=True):
                    child.terminate()
                parent.terminate()
                process.wait()
        except Exception as e:
            print(f"Error stopping RTSP server {stream_id}: {e}")

atexit.register(cleanup)

# Mount static files
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
        # Enable CORS for all static files
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

app.mount("/static", CustomStaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Store chunk information for each task
chunk_storage = {}

# Store conversion tasks
conversion_tasks = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload/")
async def upload_video(
    file: UploadFile,
    media_format: str = Form(...),
    streaming_protocol: str = Form(...)
):
    # Create output directory based on input filename (without extension)
    file_base = os.path.splitext(file.filename)[0]
    output_dir = os.path.join(OUTPUT_DIR, file_base)
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    output_name = file_base  # Use base name without extension
    
    # Set output path based on format
    if media_format == 'hls':
        output_path = os.path.join(output_dir, 'playlist.m3u8')
    elif media_format == 'dash':
        output_path = os.path.join(output_dir, 'playlist.mpd')
    else:
        output_path = os.path.join(output_dir, 'output.mp4')
    
    # Save the file
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Store conversion task
    task_id = len(conversion_tasks) + 1
    conversion_tasks[task_id] = {
        'input': file_path,
        'output': output_path,
        'media_format': media_format,
        'streaming_protocol': streaming_protocol,
        'status': 'pending'
    }
    
    # Start conversion (in a real app, use a background task or queue)
    try:
        await convert_video(task_id)
        return {"task_id": task_id, "status": "processing", "message": "Conversion started"}
    except Exception as e:
        conversion_tasks[task_id]['status'] = 'failed'
        raise HTTPException(status_code=500, detail=str(e))

def get_stream_url(task_id: int):
    task = conversion_tasks.get(task_id)
    if not task:
        return None
    
    file_base = os.path.splitext(os.path.basename(task['input']))[0]
    
    if task['streaming_protocol'] == 'hls':
        return {"type": "hls", "url": f"/static/output/{file_base}/playlist.m3u8"}
    elif task['streaming_protocol'] == 'dash':
        return {"type": "dash", "url": f"/static/output/{file_base}/playlist.mpd"}
    elif task['streaming_protocol'] == 'rtsp':
        # For RTSP, we'll return the RTSP URL
        stream_id = task.get('stream_id', str(uuid.uuid4()))
        rtsp_url = f"rtsp://localhost:{RTSP_PORT}/{stream_id}"
        return {"type": "rtsp", "url": rtsp_url, "stream_id": stream_id}
    return None

async def start_rtsp_stream(input_path: str, stream_id: str):
    """Start an RTSP server for the given input file"""
    # Stop any existing server with the same stream_id
    if stream_id in rtsp_servers:
        cleanup_stream(stream_id)
    
    # Create RTSP server command
    rtsp_cmd = [
        'ffmpeg',
        '-re',  # Read input at native frame rate
        '-stream_loop', '-1',  # Loop the input
        '-i', input_path,
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-tune', 'zerolatency',
        '-f', 'rtsp',
        f'rtsp://0.0.0.0:{RTSP_PORT}/{stream_id}'
    ]
    
    # Start the RTSP server in a subprocess
    process = await asyncio.create_subprocess_exec(
        *rtsp_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Store the process for later cleanup
    rtsp_servers[stream_id] = process
    
    # Wait a moment to ensure the server starts
    await asyncio.sleep(1)
    return process

def cleanup_stream(stream_id: str):
    """Clean up an RTSP stream"""
    if stream_id in rtsp_servers:
        process = rtsp_servers.pop(stream_id)
        try:
            if process and process.returncode is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        except Exception as e:
            print(f"Error cleaning up RTSP stream {stream_id}: {e}")

async def convert_video(task_id: int):
    task = conversion_tasks[task_id]
    task['status'] = 'processing'
    task['stream_id'] = task.get('stream_id', str(uuid.uuid4()))  # Generate a unique stream ID
    
    try:
        if task['streaming_protocol'] == 'hls':
            # HLS conversion
            # Ensure output directory exists
            # HLS format
            output_name = os.path.basename(task['output'])
            output_dir = os.path.join(OUTPUT_DIR, os.path.splitext(os.path.basename(task['input']))[0])
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, 'playlist.m3u8')
            
            # Create HLS stream with multiple bitrates
            cmd = [
                'ffmpeg',
                '-i', task['input'],
                
                # Video codec configuration
                '-map', '0:v:0',
                '-c:v:0', 'libx264',
                '-b:v:0', '2000k',
                '-maxrate:v:0', '2200k',
                '-bufsize:v:0', '4000k',
                '-profile:v:0', 'high',
                '-level', '4.0',
                '-x264opts', 'keyint=60:min-keyint=60:no-scenecut',
                '-g', '60',
                '-sc_threshold', '0',
                
                # Audio configuration
                '-map', '0:a:0',
                '-c:a:0', 'aac',
                '-b:a:0', '128k',
                '-ac', '2',
                
                # HLS settings
                '-f', 'hls',
                '-hls_time', '6',
                '-hls_list_size', '0',
                '-hls_flags', 'independent_segments',
                '-hls_segment_type', 'mpegts',
                '-hls_segment_filename', f'{output_dir}/segment_%v_%03d.ts',
                '-master_pl_name', 'playlist.m3u8',
                '-var_stream_map', 'v:0,a:0',
                '-hls_playlist_type', 'vod',
                '-method', 'PUT',
                output_dir + '/stream_%v.m3u8'
            ]
        else:  # DASH
            # DASH conversion
            # Ensure output directory exists
            output_dir = os.path.join(OUTPUT_DIR, os.path.splitext(os.path.basename(task['input']))[0])
            os.makedirs(output_dir, exist_ok=True)
            
            cmd = [
                'ffmpeg',
                '-i', task['input'],
                
                # Video representations
                '-map', '0:v:0',
                '-c:v:0', 'libx264',
                '-b:v:0', '2000k',
                '-maxrate:v:0', '2200k',
                '-bufsize:v:0', '4000k',
                '-profile:v:0', 'high',
                '-level:v:0', '4.0',
                '-x264opts', 'keyint=60:min-keyint=60:no-scenecut',
                '-g', '60',
                '-sc_threshold', '0',
                
                # Audio representation
                '-map', '0:a:0',
                '-c:a:0', 'aac',
                '-b:a:0', '128k',
                '-ac', '2',
                
                # DASH settings
                '-f', 'dash',
                '-use_template', '1',
                '-use_timeline', '1',
                '-seg_duration', '6',
                '-frag_duration', '6',
                '-frag_type', 'duration',
                '-window_size', '5',
                '-extra_window_size', '5',
                '-remove_at_exit', '1',
                '-adaptation_sets', 'id=0,streams=v id=1,streams=a',
                task['output']
            ]
        
        if task['streaming_protocol'] == 'rtsp':
            # For RTSP, start the streaming server
            print(f"Starting RTSP server for {task['input']}")
            process = await start_rtsp_stream(task['input'], task['stream_id'])
            if process.returncode is not None:
                error_msg = await process.stderr.read()
                error_msg = error_msg.decode()
                print(f"RTSP server error: {error_msg}")
                raise Exception(f"Failed to start RTSP server: {error_msg}")
            print(f"RTSP server started at rtsp://localhost:{RTSP_PORT}/{task['stream_id']}")
            task['status'] = 'completed'
            task['stream_url'] = await get_stream_url(task_id)
        else:
            # For HLS/DASH, process the file
            print(f"Running command: {' '.join(cmd)}")
                    
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode()
                print(f"FFmpeg error: {error_msg}")
                raise Exception(f"FFmpeg error: {error_msg}")
            
            task['status'] = 'completed'
            task['stream_url'] = await get_stream_url(task_id)
        
    except Exception as e:
        task['status'] = 'failed'
        task['error'] = str(e)
        raise

@app.get("/task/{task_id}")
async def get_task_status(task_id: int):
    task = conversion_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "status": task['status'],
        "stream_url": task.get('stream_url'),
        "error": task.get('error')
    }

@app.get("/stream/{task_id}")
async def get_stream_url(task_id: int):
    if task_id not in conversion_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = conversion_tasks[task_id]
    if task.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Conversion not complete")
    
    try:
        # Initialize chunk storage for this task if it doesn't exist
        if task_id not in chunk_storage:
            chunk_storage[task_id] = {
                'hls_chunks': [],
                'dash_chunks': []
            }
            
            # Get the base output directory
            file_base = os.path.splitext(os.path.basename(task['input']))[0]
            output_dir = os.path.join("static", "output", file_base)
            
            # Scan for HLS chunks
            hls_dir = output_dir
            if os.path.exists(hls_dir):
                chunk_storage[task_id]['hls_chunks'] = [
                    str(f) for f in os.listdir(hls_dir) 
                    if f.endswith(('.ts', '.m3u8'))
                ]
            
            # Scan for DASH chunks
            dash_dir = os.path.join(output_dir, "dash")
            if os.path.exists(dash_dir):
                chunk_storage[task_id]['dash_chunks'] = [
                    str(f) for f in os.listdir(dash_dir) 
                    if f.endswith(('.m4s', '.mpd', '.init.mp4'))
                ]
        
        # Get the base URL path
        file_base = os.path.splitext(os.path.basename(task['input']))[0]
        base_url = f"/static/output/{file_base}"
        
        # Create a serializable response with all values as plain data (no coroutines)
        response = {
            "hls_url": f"{base_url}/playlist.m3u8" if task.get('streaming_protocol') == 'hls' else None,
            "dash_url": f"{base_url}/dash/playlist.mpd" if task.get('streaming_protocol') == 'dash' else None,
            "rtsp_url": f"rtsp://localhost:{RTSP_PORT}/{task.get('stream_id', '')}" if task.get('streaming_protocol') == 'rtsp' else None,
            "chunks_available": bool(chunk_storage.get(task_id, {}).get('hls_chunks') or chunk_storage.get(task_id, {}).get('dash_chunks')),
            "streaming_protocol": task.get('streaming_protocol'),
            "status": task.get('status', 'unknown')
        }
        
        return response
        
    except Exception as e:
        # If there's an error, return a basic response without chunk info
        return {
            "error": f"Could not load stream information: {str(e)}",
            "status": task.get('status', 'error')
        }
        
@app.get("/chunks/{task_id}")
async def get_chunk_content(
    task_id: int,
    chunk_name: str = Query(..., description="Name of the chunk file to retrieve"),
    chunk_type: str = Query(..., description="Type of chunk: 'hls' or 'dash'")
):
    """
    Retrieve a specific chunk file (TS, M4S, M3U8, or MPD) for a given task.
    """
    try:
        if task_id not in conversion_tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Security check to prevent directory traversal
        if '..' in chunk_name or '/' in chunk_name or '\\' in chunk_name:
            raise HTTPException(status_code=400, detail="Invalid chunk name")
        
        chunk_type = chunk_type.lower()
        if chunk_type not in ['hls', 'dash']:
            raise HTTPException(status_code=400, detail="Invalid chunk type")
        
        # Build the file path based on chunk type
        if chunk_type == 'hls':
            file_path = os.path.join("static", "output", str(task_id), chunk_name)
        else:  # dash
            file_path = os.path.join("static", "output", str(task_id), "dash", chunk_name)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Chunk not found")
        
        # Determine content type based on file extension
        content_type = "application/octet-stream"
        if chunk_name.endswith('.m3u8'):
            content_type = "application/vnd.apple.mpegurl"
        elif chunk_name.endswith('.ts'):
            content_type = "video/MP2T"
        elif chunk_name.endswith('.mpd'):
            content_type = "application/dash+xml"
        elif chunk_name.endswith(('.m4s', '.mp4')):
            content_type = "video/mp4"
        
        # Return the file using FileResponse
        return FileResponse(
            path=file_path,
            media_type=content_type,
            filename=os.path.basename(chunk_name)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as they are
        raise
    except Exception as e:
        # Log the error for debugging
        print(f"Error serving chunk {chunk_name}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving chunk: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
