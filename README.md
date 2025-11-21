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

## API Overview

- **Base URL**: `http://localhost:8000`
- **API base prefix**: `/api/v1`
- **Interactive docs (Swagger)**: `GET /docs`

### Upload API

| 항목 | 내용 |
|------|------|
| **HTTP Method** | `POST` |
| **URL** | `/api/v1/upload/` |
| **Request Body (form-data)** | `file` (MP4 파일, 필수)  ·  `media_format` = `hls` \| `ts` \| `cmaf` \| `dash`  ·  `streaming_protocol` = `hls` \| `dash` \| `rtsp`  ·  `segment_duration` (int, 기본값 6)  ·  `crf` (int, 기본값 20)  ·  `resolution` = `source` \| `360p` \| `720p` \| `1080p` |
| **Success Response (200)** | JSON 객체: `task_id` (작업 ID), `status` (예: `processing`), `output_path` (출력 파일/플레이리스트 경로), `stream_url` (`/api/v1/stream/{task_id}`), `status_url` (`/api/v1/tasks/{task_id}`) |

### Task APIs

#### 단일 작업 상태 조회

| 항목 | 내용 |
|------|------|
| **HTTP Method** | `GET` |
| **URL** | `/api/v1/tasks/{task_id}` |
| **Path Params** | `task_id` (int) – 업로드/변환 작업 ID |
| **Success Response (200)** | JSON 객체: `task_id`, `status`, `progress`, `error`, `stream_url` |

#### 작업 리스트 조회

| 항목 | 내용 |
|------|------|
| **HTTP Method** | `GET` |
| **URL** | `/api/v1/tasks/` |
| **Query Params** | 없음 |
| **Success Response (200)** | 작업별 `task_id`, `status`, `filename`, `created_at` 를 담은 리스트 |

### Streaming APIs

#### 스트림 정보 조회

| 항목 | 내용 |
|------|------|
| **HTTP Method** | `GET` |
| **URL** | `/api/v1/stream/{task_id}` |
| **Path Params** | `task_id` (int) – 업로드/변환 작업 ID |
| **Success Response (200)** | JSON 객체: `hls_url`, `dash_url`, `rtsp_url`, `streaming_protocol` (`hls`/`dash`/`rtsp`), `status` |

#### 세그먼트(Chunk) 파일 조회

| 항목 | 내용 |
|------|------|
| **HTTP Method** | `GET` |
| **URL** | `/api/v1/chunks/{task_id}` |
| **Path Params** | `task_id` (int) – 업로드/변환 작업 ID |
| **Query Params** | `chunk_name` (예: `playlist.m3u8`, `segment_000.ts`, `playlist.mpd` 등), `chunk_type` = `hls` \| `dash` |
| **Success Response (200)** | 요청한 미디어 조각 파일 (`FileResponse`) |

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
