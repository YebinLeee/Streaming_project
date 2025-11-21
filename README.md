# Video Streaming Application

A powerful web application for uploading videos and streaming them using HLS, DASH, or RTSP protocols with adaptive bitrate streaming and resolution control.

## Features
![Streaming UI](docs/image.png)
- 🎥 Upload MP4 videos
- 🔄 Multiple media format support for packaging (output layout):
  - **HLS**: `playlist.m3u8` + `*.ts` segments
  - **DASH**: `playlist.mpd` + fragmented MP4 (`*.m4s`, `init-*.mp4`) segments
  - **CMAF**: CMAF (Common Media Application Format) fragmented MP4 – 공통 fMP4 자산을 만들어 두고, 이를 HLS나 DASH 매니페스트에서 재사용할 수 있는 형식
  - **RTSP (TS)**: MPEG‑TS over RTSP for low-latency streaming
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
   docker compose up --build
   ```

3. **Access the application**:
   - Web interface: http://localhost:8000
   - API documentation: http://localhost:8000/docs

4. **Stopping the application**:
   ```bash
   docker compose down
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
   - Select the desired **media format** (패키징 방식)
     - `hls`  → HLS: `m3u8 + TS` 세그먼트
     - `dash` → DASH: `mpd + fMP4` 세그먼트
     - `cmaf` → CMAF 기반 패키징 (공통 fMP4 세그먼트를 생성하고, 이를 HLS/DASH에서 사용할 수 있음)
     - `ts`   → TS 기반 패키징 (내부적으로 HLS 파이프라인을 사용, 주로 RTSP와 조합)
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

## API Overview

- **Base URL**: `http://localhost:8000`
- **API base prefix**: `/api/v1`
- **Interactive docs (Swagger)**: `GET /docs`

### Upload API

| 항목 | 내용 |
|------|------|
| **HTTP Method** | `POST` |
| **URL** | `/api/v1/upload/` |

| **Request Body (form-data)** | 
|--------|
`- file`: MP4 파일, 필수<br>
`- media_format`: hls(m3u8/ts) \| mpeg2-ts \| cmaf(mpd/fmp4) \| dash(mpd/fmp4) <br>
`- streaming_protocol`: hls \| dash \| rtsp <br>
`- segment_duration` (int, 기본값 6) <br>
`- crf` (int, 기본값 20) <br>
`- resolution`: source \| 360p \| 720p \| 1080p |

| **Success Response (200)** | 
|--------|
JSON<br>
`- task_id`: 생성된 작업 ID<br>
`- status`: 작업 상태 (예: processing)<br>
`- output_path`: 생성된 출력 파일/플레이리스트 경로<br>
`- stream_url`: 스트림 정보를 조회하는 엔드포인트 (예: /api/v1/stream/{task_id})<br>
`- status_url`: 작업 상태 조회 엔드포인트 (예: /api/v1/tasks/{task_id}) |

#### 예시 Request Body (multipart/form-data 개념 JSON 표현)

```json
{
  "file": "<binary MP4>",
  "media_format": "hls",
  "streaming_protocol": "hls",
  "segment_duration": 6,
  "crf": 20,
  "resolution": "source"
}
```

#### 예시 Success Response (200)

```json
{
  "task_id": 1,
  "status": "processing",
  "message": "Upload and conversion started",
  "output_path": "static/output/example_1234/playlist.m3u8",
  "stream_url": "/api/v1/stream/1",
  "status_url": "/api/v1/tasks/1"
}
```

### Task APIs

#### 단일 작업 상태 조회

| 항목 | 내용 |
|------|------|
| **HTTP Method** | `GET` |
| **URL** | `/api/v1/tasks/{task_id}` |

| **Path Params** | 
|-----------|
- `task_id` (int): 업로드/변환 작업 ID 

| **Success Response (200)** | 
|----------|
JSON 객체<br>
`- task_id`<br>
`- status`<br>
`- progress`<br>
`- error`<br>
`- stream_url` |

##### 예시 Response (200)

```json
{
  "task_id": 1,
  "status": "completed",
  "progress": 100,
  "error": null,
  "stream_url": "/api/v1/stream/1"
}
```

#### 작업 리스트 조회

| 항목 | 내용 |
|------|------|
| **HTTP Method** | `GET` |
| **URL** | `/api/v1/tasks/` |


| **Success Response (200)** | 
|----------|
작업 리스트<br>
각 항목: `task_id`, `status`, `filename`, `created_at` |

##### 예시 Response (200)

```json
[
  {
    "task_id": 1,
    "status": "completed",
    "filename": "example_1234.mp4",
    "created_at": "2025-11-21T01:23:45Z"
  },
  {
    "task_id": 2,
    "status": "processing",
    "filename": "sample_5678.mp4",
    "created_at": "2025-11-21T01:25:10Z"
  }
]
```

### Streaming APIs

#### 스트림 정보 조회

| 항목 | 내용 |
|------|------|
| **HTTP Method** | `GET` |
| **URL** | `/api/v1/stream/{task_id}` |

| **Path Params** | 
|-----------|
`- task_id` (int): 업로드/변환 작업 ID |

| **Success Response (200)** | 
|----------|
JSON 객체<br>
`- hls_url`<br>
`- dash_url`<br>
`- rtsp_url`<br>
`- streaming_protocol` (`hls`/`dash`/`rtsp`)<br>
`- status` |

##### 예시 Response (200)

```json
{
  "hls_url": "/static/output/example_1234/playlist.m3u8",
  "dash_url": null,
  "rtsp_url": null,
  "streaming_protocol": "hls",
  "status": "completed"
}
```

#### 세그먼트(Chunk) 파일 조회

| 항목 | 내용 |
|------|------|
| **HTTP Method** | `GET` |
| **URL** | `/api/v1/chunks/{task_id}` |

| **Path Params** | 
|-----------|
`- task_id` (int): 업로드/변환 작업 ID |

| **Query Params** | 
|-----------|
`- chunk_name` (예: `playlist.m3u8`, `segment_000.ts`, `playlist.mpd` 등)<br>
`- chunk_type` = `hls` \| `dash` |

| **Success Response (200)** | 
|----------|
요청한 미디어 조각 파일 (`FileResponse`) |

#### 예시 Query + Response

- Request 예시:

```http
GET /api/v1/chunks/1?chunk_name=playlist.m3u8&chunk_type=hls
```

- Response: HLS 플레이리스트 텍스트 (`application/vnd.apple.mpegurl`)


## Media Format and Protocol Compatibility

> **Note**: `media_format`는 출력 파일 구조(패키징)를 의미하고,
> `streaming_protocol`은 클라이언트가 접근하는 방법(HLS/DASH/RTSP)을 의미합니다.

| Packaging format (media_format 기준) | HLS (HTTP) | MPEG-DASH (HTTP) | RTSP |
|--------------------------------------|------------|-------------------|------|
| HLS (`hls`) – `m3u8 + TS`            | O          | X                 | X    |
| DASH (`dash`) – `mpd + fMP4`         | X          | O                 | X    |
| TS (`ts`) – MPEG‑TS segments         | X          | X                 | O*   |
| CMAF (`cmaf`) – CMAF fMP4 segments   | O (HLS에서 사용 가능) | O (DASH에서 사용 가능) | X    |

`*` TS 포맷은 내부적으로 HLS 파이프라인을 사용하지만, 주 사용 목적은 RTSP(MPEG‑TS over RTSP)와의 조합입니다.

### RTSP Playback Example

- **기본 RTSP 포트**: `8554` (환경변수 `RTSP_PORT`로 설정 가능)
- 업로드 시 `streaming_protocol=rtsp` 로 작업을 생성하면, 내부적으로 FFmpeg RTSP 서버가 다음과 같이 뜹니다.

#### 예시 RTSP URL

- 로컬 서버 기준:
  - `rtsp://localhost:8554/<stream_id>`
  - 예: `rtsp://localhost:8554/1`
- 원격 서버(예: 192.168.0.10) 기준:
  - `rtsp://192.168.0.10:8554/<stream_id>`

`stream_id`는 업로드/변환 작업에 매핑된 스트림 ID이며, RTSP 전용 업로드 후 `/api/v1/stream/{task_id}` 응답의 `rtsp_url` 필드에서 확인할 수 있습니다.

#### VLC에서 여는 방법

1. VLC 실행
2. **Media → Open Network Stream...** 메뉴 선택
3. "Network URL" 입력 필드에 위의 RTSP URL 입력 (예: `rtsp://localhost:8554/1`)
4. **Play** 버튼 클릭 → RTSP 스트림 재생

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
