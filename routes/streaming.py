from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
from app import app, conversion_tasks, chunk_storage, OUTPUT_DIR, rtsp_servers
from pathlib import Path

router = APIRouter(tags=["streaming"])

@router.get("/stream/{task_id}")
async def get_stream(task_id: int):
    if task_id not in conversion_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = conversion_tasks[task_id]
    if task["status"] != "completed":
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
        
        # Create response with stream information
        response = {
            "hls_url": f"{base_url}/playlist.m3u8" if task.get('streaming_protocol') == 'hls' else None,
            "dash_url": f"{base_url}/dash/playlist.mpd" if task.get('streaming_protocol') == 'dash' else None,
            "rtsp_url": f"rtsp://localhost:8554/{task.get('stream_id', '')}" if task.get('streaming_protocol') == 'rtsp' else None,
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

@router.get("/chunks/{task_id}")
async def get_chunk_content(
    task_id: int,
    chunk_name: str,
    chunk_type: str
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
        file_base = os.path.splitext(os.path.basename(conversion_tasks[task_id]['input']))[0]
        if chunk_type == 'hls':
            file_path = os.path.join("static", "output", file_base, chunk_name)
        else:  # dash
            file_path = os.path.join("static", "output", file_base, "dash", chunk_name)
        
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
