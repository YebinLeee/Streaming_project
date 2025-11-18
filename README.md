# Video Streaming Application

A powerful web application for uploading videos and streaming them using HLS, DASH, or RTSP protocols with adaptive bitrate streaming and resolution control.

## Features

- 🎥 Upload MP4 videos
- 🔄 Multiple media format support for packaging:
  - HLS (m3u8/ts)
  - TS (Transport Stream)
  - fMP4/MPD (MPEG-DASH)
  - CMAF (supports both HLS and DASH)
- 🌐 Streaming protocols:
  - HLS (HTTP Live Streaming)
  - MPEG-DASH
  - RTSP (Real Time Streaming Protocol)
- 🎚️ Adaptive bitrate streaming
- 🖥️ Resolution control (client-side)
- 🌈 Network condition simulation
- 📱 Responsive web interface

## Prerequisites

- Docker and Docker Compose (recommended)
- Or manually:
  - Python 3.7+
  - FFmpeg
  - Node.js and npm (for frontend dependencies)

## Docker Installation (Recommended)

1. **Clone the repository** (if not already done):
   ```bash
   git clone https://github.com/YebinLeee/Streaming_project.git
   cd Streaming_project
   ```

2. **Build and start the containers**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - Web interface: http://localhost:8000
   - API documentation: http://localhost:8000/docs

4. **Stopping the application**:
   ```bash
   docker-compose down
   ```

## Manual Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd streaming-app
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install FFmpeg:
   - On macOS: `brew install ffmpeg`
   - On Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - On Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Running the Application

1. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

## Usage

1. **Upload Video**
   - Click "Choose File" to select an MP4 video file
   - Select the desired media format (HLS, DASH, RTSP, or CMAF)
   - The compatible streaming protocols will be automatically enabled/disabled
   - Click "Upload & Convert"

2. **Playback Controls**
   - Use the player controls to play/pause the video
   - Adjust volume using the volume slider
   - Toggle fullscreen mode

3. **Resolution Control**
   - Available resolutions will be detected automatically
   - Click any resolution button to switch quality
   - The player will smoothly transition between qualities

4. **Network Simulation**
   - Test different network conditions:
     - No throttling (full speed)
     - Fast 3G (~1.5 Mbps)
     - Slow 3G (~400 Kbps)
     - Custom bitrate
   - The player will automatically adapt to the selected network condition

## Media Format and Protocol Compatibility

| | HLS | MPEG-DASH | RTSP |
|--------------|-----|-----------|------|
| HLS (m3u8/ts)  | O  | X        | X   |
| MPEG-DASH (mpd/ts)    | X  | O        | X   |
| RTSP (MPEG-2 TS)    | X  | X        | O   |
| CMAF (m3u8/ts/mpd/ts)         | O  | O        | X   |

## Docker Configuration

The Docker setup includes:

- **Ports**:
  - `8000`: Web interface and API
  - `8554`: RTSP streaming port

- **Volumes**:
  - `./uploads`: Uploaded video files
  - `./static/output`: Processed streaming files

- **Environment Variables**:
  - `UPLOAD_DIR`: Directory for uploaded files (default: `/app/uploads`)
  - `OUTPUT_DIR`: Directory for processed files (default: `/app/static/output`)
  - `RTSP_PORT`: RTSP streaming port (default: `8554`)

## Project Structure

- `main.py`: FastAPI application and API endpoints
- `templates/`: HTML templates
  - `index.html`: Main application interface
- `static/`: Static files (CSS, JS, output videos)
- `uploads/`: Temporary storage for uploaded files

## License

MIT
