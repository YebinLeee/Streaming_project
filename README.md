# Video Streaming Application

A powerful web application for uploading videos and streaming them using HLS, DASH, or RTSP protocols with adaptive bitrate streaming and resolution control.

## Features
![Streaming UI](docs/image.png)
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
- 🎚️ Encoding controls per upload:
  - Segment duration (seconds) for HLS/DASH/CMAF
  - CRF (H.264 quality, lower = higher quality)
  - Output resolution toggle (Source / 360p / 720p / 1080p)
- 🧭 Segment navigation UI:
  - Shows currently loaded HLS/DASH segments while playing
  - Click a segment badge to seek playback to that segment position
- 📱 Responsive web interface

![Streaming UI](docs/image_view.png)

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
   - Select the desired media format (HLS, DASH, TS, or CMAF)
   - The compatible streaming protocols will be automatically enabled/disabled
   - Choose **Segment Duration** (seconds) for generated chunks
   - Set **CRF** (video quality, typical range 18–24)
   - Choose **Resolution** (Source / 360p / 720p / 1080p)
   - Click "Upload & Convert" to start packaging and transcoding

2. **Playback Controls**
   - Use the player controls to play/pause the video
   - Adjust volume using the volume slider
   - Toggle fullscreen mode

3. **Resolution / Quality Control**
   - Effective output resolution and quality are determined at upload time by the selected **Resolution** and **CRF** values
   - Lower resolution and higher CRF values produce smaller files but lower visual quality

4. **Segment Navigation (HLS / DASH)**
   - While playing a HLS or MPEG-DASH stream, the app displays the list of recently loaded segments under the player
   - The currently playing segment is highlighted
   - Click any segment badge to seek playback to that segment (approximate start time = segment index × segment duration)

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
