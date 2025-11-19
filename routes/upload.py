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
    streaming_protocol: str = Form(...),
    segment_duration: int = Form(6)
):
    task_id = None
    try:
        print(f"Received upload request for file: {file.filename}")
        
        # Ensure upload directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Create output directory based on input filename (without extension) with unique ID
        file_base = os.path.splitext(file.filename)[0]
        unique_id = str(uuid.uuid4())[:8]
        output_dir = os.path.join(OUTPUT_DIR, f"{file_base}_{unique_id}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the uploaded file with a unique name to avoid conflicts
        file_ext = os.path.splitext(file.filename)[1]
        saved_filename = f"{file_base}_{unique_id}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, saved_filename)
        
        print(f"Saving file to: {file_path}")
        
        # Save the file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        print(f"File saved successfully. Size: {os.path.getsize(file_path)} bytes")
        
        # Set output path based on format
        # Frontend sends: hls, ts, cmaf, dash
        # - hls           -> HLS (.m3u8)
        # - ts            -> HLS (.m3u8) but RTSP 프로토콜에서 사용 (TS 기반)
        # - cmaf + hls    -> HLS (.m3u8) 로 취급 (CMAF-HLS 조합)
        # - cmaf + dash   -> DASH (.mpd)
        # - dash          -> DASH (.mpd)

        original_media_format = media_format

        if media_format == 'hls':
            media_format = 'hls'
            output_path = os.path.join(output_dir, 'playlist.m3u8')
        elif media_format == 'ts':
            # TS 포맷은 내부적으로 HLS 파이프라인을 사용하되,
            # 스트리밍 프로토콜에서 RTSP 를 선택하도록 UI에서 제한함.
            media_format = 'hls'
            output_path = os.path.join(output_dir, 'playlist.m3u8')
        elif media_format == 'cmaf':
            # CMAF + HLS  -> HLS(.m3u8)
            # CMAF + DASH -> DASH(.mpd) in 'dash' subdirectory
            if streaming_protocol == 'hls':
                media_format = 'hls'
                output_path = os.path.join(output_dir, 'playlist.m3u8')
            else:
                media_format = 'dash'
                dash_dir = os.path.join(output_dir, 'dash')
                os.makedirs(dash_dir, exist_ok=True)
                output_path = os.path.join(dash_dir, 'playlist.mpd')
        elif media_format == 'dash':
            # DASH -> DASH(.mpd) in 'dash' subdirectory
            media_format = 'dash'
            dash_dir = os.path.join(output_dir, 'dash')
            os.makedirs(dash_dir, exist_ok=True)
            output_path = os.path.join(dash_dir, 'playlist.mpd')
        else:
            # fallback: mp4 파일 그대로 저장하는 경우 등
            output_path = os.path.join(output_dir, 'output.mp4')
            
        print(f"Output will be saved to: {output_path}")
        
        # Create task entry
        task_id = len(conversion_tasks) + 1
        conversion_tasks[task_id] = {
            'input': file_path,
            'output': output_path,
            'media_format': media_format,
            'streaming_protocol': streaming_protocol,
            'segment_duration': int(segment_duration),
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
