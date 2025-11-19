from fastapi import APIRouter, UploadFile, Form, HTTPException, File
import os
import shutil
import uuid
from pathlib import Path
from app import app, conversion_tasks, UPLOAD_DIR, OUTPUT_DIR, RTSP_PORT
import asyncio
from services.video_converter import convert_video

router = APIRouter(tags=["upload"])

@router.post("/upload/")
async def upload_video(
    file: UploadFile = File(...),
    media_format: str = Form(...),
    streaming_protocol: str = Form(...)
):
    task_id = None
    try:
        print(f"Received upload request for file: {file.filename}")
        
        # Ensure upload directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Create output directory based on input filename (without extension)
        file_base = os.path.splitext(file.filename)[0]
        output_dir = os.path.join(OUTPUT_DIR, file_base)
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the uploaded file with a unique name to avoid conflicts
        file_ext = os.path.splitext(file.filename)[1]
        unique_id = str(uuid.uuid4())[:8]
        saved_filename = f"{file_base}_{unique_id}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, saved_filename)
        
        print(f"Saving file to: {file_path}")
        
        # Save the file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        print(f"File saved successfully. Size: {os.path.getsize(file_path)} bytes")
        
        # Set output path based on format
        if media_format == 'hls':
            output_path = os.path.join(output_dir, 'playlist.m3u8')
        elif media_format == 'dash':
            output_path = os.path.join(output_dir, 'playlist.mpd')
        else:
            output_path = os.path.join(output_dir, 'output.mp4')
            
        print(f"Output will be saved to: {output_path}")
        
        # Create task entry
        task_id = len(conversion_tasks) + 1
        conversion_tasks[task_id] = {
            'input': file_path,
            'output': output_path,
            'media_format': media_format,
            'streaming_protocol': streaming_protocol,
            'status': 'pending',
            'progress': 0,
            'error': None
        }
        
        print(f"Created task {task_id} for {file.filename}")
        
        # Start conversion in the background
        try:
            asyncio.create_task(
                convert_video(
                    task_id=task_id,
                    conversion_tasks=conversion_tasks,
                    output_dir=output_dir,
                    rtsp_port=RTSP_PORT
                )
            )
            conversion_tasks[task_id]['status'] = 'processing'
            print(f"Started background conversion for task {task_id}")
            
            return {
                "task_id": task_id,
                "status": "processing",
                "message": "Upload and conversion started",
                "output_path": output_path,
                "stream_url": f"/api/v1/stream/{task_id}",
                "status_url": f"/api/v1/tasks/{task_id}"
            }
            
        except Exception as e:
            error_msg = f"Failed to start conversion task: {str(e)}"
            print(error_msg)
            if task_id in conversion_tasks:
                conversion_tasks[task_id]['status'] = 'failed'
                conversion_tasks[task_id]['error'] = error_msg
            raise HTTPException(status_code=500, detail=error_msg)
            
    except Exception as e:
        error_msg = f"Error during upload: {str(e)}"
        print(error_msg)
        if task_id and task_id in conversion_tasks:
            conversion_tasks[task_id]['status'] = 'failed'
            conversion_tasks[task_id]['error'] = error_msg
        raise HTTPException(status_code=500, detail=error_msg)
