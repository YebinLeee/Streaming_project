import os
import subprocess
import asyncio
import psutil
from pathlib import Path
from typing import Dict, Any

# Store RTSP server processes
rtsp_servers: Dict[str, Any] = {}

async def convert_video(task_id: int, conversion_tasks: dict, output_dir: str, rtsp_port: int = 8554):
    """
    Convert video to the specified format and protocol
    """
    if task_id not in conversion_tasks:
        print(f"Task {task_id} not found in conversion_tasks")
        return
        
    task = conversion_tasks[task_id]
    task['status'] = 'processing'
    print(f"Starting conversion for task {task_id}")
    print(f"Input: {task.get('input')}")
    print(f"Output: {task.get('output')}")
    print(f"Format: {task.get('media_format')}")
    print(f"Protocol: {task.get('streaming_protocol')}")
    
    try:
        input_path = task.get('input')
        output_path = task.get('output')
        media_format = task.get('media_format')
        streaming_protocol = task.get('streaming_protocol')
        
        # Validate required fields
        if not all([input_path, output_path, media_format, streaming_protocol]):
            raise ValueError("Missing required task parameters")
            
        print(f"Starting {streaming_protocol.upper()} conversion for {input_path}")
        print(f"Output will be saved to: {output_path}")
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        print(f"Ensured output directory exists: {output_dir}")
        
        # Verify input file exists
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if streaming_protocol == 'hls':
            await _convert_to_hls(input_path, output_path, task_id, conversion_tasks)
        elif streaming_protocol == 'dash':
            await _convert_to_dash(input_path, output_path, task_id, conversion_tasks)
        elif streaming_protocol == 'rtsp':
            await _start_rtsp_stream(input_path, str(task_id), rtsp_port, task_id, conversion_tasks)
        
        task['status'] = 'completed'
        print(f"Successfully completed conversion for task {task_id}")
        
    except Exception as e:
        error_msg = f"Error in convert_video: {str(e)}"
        print(error_msg)
        task['status'] = 'failed'
        task['error'] = error_msg
        # Don't re-raise to prevent unhandled exceptions in the background task
        print(f"Task {task_id} failed: {error_msg}")

async def _convert_to_hls(input_path: str, output_path: str, task_id: int, conversion_tasks: dict):
    """Convert video to HLS format"""
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output files without asking
        '-i', input_path,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-hls_time', '6',
        '-hls_playlist_type', 'vod',
        '-hls_segment_filename', output_path.replace('.m3u8', '_%03d.ts'),
        '-hls_flags', 'independent_segments',
        '-start_number', '0',  # Start segment numbering from 0
        output_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    await process.wait()
    
    if process.returncode != 0:
        error = await process.stderr.read()
        raise Exception(f"FFmpeg error: {error.decode()}")

async def _convert_to_dash(input_path: str, output_path: str, task_id: int, conversion_tasks: dict):
    """Convert video to DASH format"""
    output_dir = os.path.dirname(output_path)
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output files without asking
        '-i', input_path,
        '-map', '0:v:0',
        '-map', '0:a:0',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-f', 'dash',
        '-use_timeline', '1',
        '-use_template', '1',
        '-seg_duration', '6',
        '-frag_duration', '6',
        '-window_size', '5',
        '-adaptation_sets', 'id=0,streams=v id=1,streams=a',
        '-init_seg_name', 'init-stream$RepresentationID$.$ext$',
        '-media_seg_name', 'chunk-stream$RepresentationID$-$Number%05d$.$ext$',
        output_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    await process.wait()
    
    if process.returncode != 0:
        error = await process.stderr.read()
        raise Exception(f"FFmpeg error: {error.decode()}")

async def _start_rtsp_stream(input_path: str, stream_id: str, port: int, task_id: int, conversion_tasks: dict):
    """Start an RTSP stream for the input video"""
    # Stop any existing server with the same stream_id
    await _stop_rtsp_stream(stream_id)
    
    cmd = [
        'ffmpeg',
        '-re',  # Read input at native frame rate
        '-stream_loop', '-1',  # Loop the input
        '-i', input_path,
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-tune', 'zerolatency',
        '-f', 'rtsp',
        f'rtsp://0.0.0.0:{port}/{stream_id}'
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Store the process for later cleanup
    rtsp_servers[stream_id] = process
    
    # Wait a moment to ensure the server starts
    await asyncio.sleep(1)
    
    # Check if the process is still running
    if process.returncode is not None:
        error = await process.stderr.read()
        raise Exception(f"Failed to start RTSP server: {error.decode()}")
    
    # Store the RTSP URL in the task
    conversion_tasks[task_id]['rtsp_url'] = f"rtsp://localhost:{port}/{stream_id}"

async def _stop_rtsp_stream(stream_id: str):
    """Stop an RTSP stream"""
    if stream_id in rtsp_servers:
        process = rtsp_servers.pop(stream_id)
        try:
            if process and process.returncode is None:
                parent = psutil.Process(process.pid)
                for child in parent.children(recursive=True):
                    child.terminate()
                parent.terminate()
                await process.wait()
        except Exception as e:
            print(f"Error stopping RTSP server {stream_id}: {e}")
