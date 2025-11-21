#!/usr/bin/env python3
"""
Main entry point for the FastAPI application.
This file only contains the Uvicorn server configuration.
The actual FastAPI app is defined in app.py
"""
import uvicorn
from app import app

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
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1
    )
