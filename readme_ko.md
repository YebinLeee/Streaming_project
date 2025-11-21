# 비디오 스트리밍 애플리케이션

이 프로젝트는 업로드한 비디오 파일을 HLS, MPEG‑DASH, RTSP 프로토콜로 스트리밍할 수 있는 웹 애플리케이션입니다. 패키징/트랜스코딩, 기본 인코딩 설정, 생성된 세그먼트 확인 기능에 초점을 맞추고 있습니다.

## 주요 기능

![Streaming UI](docs/image.png)

- 🎥 MP4/MOV 등 일반적인 비디오 파일 업로드
- 🔄 다양한 미디어 포맷으로 패키징 (출력 레이아웃 기준)
  - **HLS**: `playlist.m3u8` + `*.ts` 세그먼트 (MPEG‑TS)
  - **DASH**: `playlist.mpd` + fragmented MP4 세그먼트 (`*.m4s`, `init-*.mp4`)
  - **CMAF**: CMAF (Common Media Application Format) fragmented MP4 – 공통 fMP4 자산을 만들어 두고 HLS/DASH 매니페스트에서 재사용 가능한 형식
  - **RTSP (TS)**: 저지연 스트리밍을 위한 MPEG‑TS over RTSP
- 🌐 지원 스트리밍 프로토콜
  - HLS (HTTP Live Streaming)
  - MPEG‑DASH
  - RTSP (Real Time Streaming Protocol)
- 🎚️ 업로드 시 인코딩 설정
  - HLS/DASH/CMAF에 사용할 세그먼트 길이 (초)
  - H.264 화질/비트레이트를 제어하기 위한 CRF 값 (낮을수록 고화질/고용량)
  - 출력 해상도 선택 (Source / 360p / 720p / 1080p)
- 🧭 세그먼트 내비게이션 UI
  - 재생 중인 HLS/DASH 세그먼트 목록을 UI에 표시
  - 세그먼트 뱃지를 클릭하면 해당 세그먼트 시점으로 시킹
- 📱 반응형 웹 UI

![Streaming UI](docs/image_view.png)

## 사전 요구 사항

- Docker 및 Docker Compose (권장)
- 또는 수동 설치 시:
  - Python 3.7+
  - FFmpeg
  - Node.js 및 npm (프론트엔드 의존성용)

## Docker로 실행 (권장)

1. **저장소 클론** (아직 하지 않았다면)

   ```bash
   git clone https://github.com/YebinLeee/Streaming_project.git
   cd Streaming_project
   ```

2. **컨테이너 빌드 및 실행**

   ```bash
   docker compose up --build
   ```

3. **애플리케이션 접속**

   - 웹 UI: http://localhost:8000
   - API 문서(Swagger): http://localhost:8000/docs

4. **애플리케이션 종료**

   ```bash
   docker compose down
   ```

## 수동 설치

1. 저장소 클론

   ```bash
   git clone <repository-url>
   cd streaming-app
   ```

2. Python 의존성 설치

   ```bash
   pip install -r requirements.txt
   ```

3. FFmpeg 설치

   - macOS: `brew install ffmpeg`
   - Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - Windows: [ffmpeg.org](https://ffmpeg.org/download.html)에서 다운로드

## 애플리케이션 실행

1. FastAPI 서버 실행

   ```bash
   uvicorn main:app --reload
   ```

2. 브라우저에서 접속

   ```
   http://localhost:8000
   ```

## 사용 방법

1. **비디오 업로드**
   - "Choose File" 버튼을 눌러 비디오 파일(MP4, MOV 등)을 선택합니다.
   - 원하는 **media_format** (패키징 방식)을 선택합니다.
     - `hls`  → HLS: `m3u8 + TS` 세그먼트
     - `dash` → DASH: `mpd + fMP4` 세그먼트
     - `cmaf` → CMAF 기반 패키징 (HLS/DASH에서 재사용 가능한 공통 fMP4 세그먼트 생성)
     - `ts`   → TS 기반 패키징 (내부적으로 HLS 파이프라인 사용, 주로 RTSP와 조합)
   - 선택한 media_format에 따라 사용 가능한 **streaming_protocol** 옵션이 자동으로 활성/비활성화됩니다.
   - **Segment Duration**(초)을 설정합니다.
   - **CRF** 값을 설정합니다 (일반적으로 18–24 권장, 낮을수록 고화질/고용량).
   - **Resolution** (Source / 360p / 720p / 1080p)을 선택합니다.
   - **Upload & Convert** 버튼을 눌러 패키징 및 트랜스코딩을 시작합니다.

2. **플레이어 컨트롤**
   - 플레이어 컨트롤로 재생/일시정지
   - 볼륨 슬라이더로 볼륨 조절
   - 전체 화면 토글

3. **해상도 / 화질 제어**
   - 업로드 시 선택한 Resolution과 CRF에 따라 실제 출력 화질과 용량이 결정됩니다.
   - 해상도를 낮추고 CRF 값을 높이면(예: 24 이상) 용량과 대역폭이 줄어드는 대신 화질이 떨어집니다.

4. **세그먼트 내비게이션 (HLS / DASH)**
   - HLS 또는 DASH 스트림 재생 중, 최근 로드된 세그먼트 목록이 플레이어 아래에 표시됩니다.
   - 현재 재생 중인 세그먼트가 강조 표시됩니다.
   - 각 세그먼트 뱃지를 클릭하면 해당 세그먼트 시점(대략 세그먼트 인덱스 × 세그먼트 길이)으로 시킹합니다.

## API 개요

- **Base URL**: `http://localhost:8000`
- **API base prefix**: `/api/v1`
- **Swagger 문서**: `GET /docs`

### Upload API

| 필드 | 설명 |
|------|------|
| **HTTP Method** | `POST` |
| **URL** | `/api/v1/upload/` |

| Request Body (form-data) | 설명 |
|--------------------------|------|
| `file` | 입력 비디오 파일 (MP4, MOV 등), 필수 |
| `media_format` | `hls` (m3u8/ts) \| `ts` (MPEG‑2 TS) \| `cmaf` (mpd/fMP4) \| `dash` (mpd/fMP4) |
| `streaming_protocol` | `hls` \| `dash` \| `rtsp` |
| `segment_duration` | 세그먼트 길이(초, 기본값: `6`) |
| `crf` | H.264 인코딩용 CRF 값 (기본값: `20`) |
| `resolution` | `source` \| `360p` \| `720p` \| `1080p` |

| Success Response (200) | 설명 |
|------------------------|------|
| JSON | `task_id`, `status`, `output_path`, `stream_url`, `status_url` 를 포함하는 응답 객체 |

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

| 필드 | 설명 |
|------|------|
| **HTTP Method** | `GET` |
| **URL** | `/api/v1/tasks/{task_id}` |

| Path Params | 설명 |
|------------|------|
| `task_id` (int) | 업로드/변환 작업 ID |

| Success Response (200) | 설명 |
|------------------------|------|
| JSON | `task_id`, `status`, `progress`, `error`, `stream_url` 를 포함하는 객체 |

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

| 필드 | 설명 |
|------|------|
| **HTTP Method** | `GET` |
| **URL** | `/api/v1/tasks/` |

| Success Response (200) | 설명 |
|------------------------|------|
| JSON 배열 | 각 항목에 `task_id`, `status`, `filename`, `created_at` 필드 포함 |

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

| 필드 | 설명 |
|------|------|
| **HTTP Method** | `GET` |
| **URL** | `/api/v1/stream/{task_id}` |

| Path Params | 설명 |
|------------|------|
| `task_id` (int) | 업로드/변환 작업 ID |

| Success Response (200) | 설명 |
|------------------------|------|
| JSON | `hls_url`, `dash_url`, `rtsp_url`, `streaming_protocol` (`hls`/`dash`/`rtsp`), `status` 포함 |

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

| 필드 | 설명 |
|------|------|
| **HTTP Method** | `GET` |
| **URL** | `/api/v1/chunks/{task_id}` |

| Path Params | 설명 |
|------------|------|
| `task_id` (int) | 업로드/변환 작업 ID |

| Query Params | 설명 |
|-------------|------|
| `chunk_name` | 파일 이름 (예: `playlist.m3u8`, `segment_000.ts`, `playlist.mpd` 등) |
| `chunk_type` | `hls` \| `dash` |

| Success Response (200) | 설명 |
|------------------------|------|
| File | 요청한 미디어 조각 파일 (`FileResponse`) |

#### 예시 Query + Response

- 요청 예시:

```http
GET /api/v1/chunks/1?chunk_name=playlist.m3u8&chunk_type=hls
```

- 응답: HLS 플레이리스트 텍스트 (`application/vnd.apple.mpegurl`)

## 미디어 포맷 및 프로토콜 호환성

> **Note**: `media_format`는 출력 파일 레이아웃(패키징)을 의미하고,
> `streaming_protocol`은 클라이언트가 스트림에 접근하는 방식(HLS/DASH/RTSP)을 의미합니다.

| Packaging format (`media_format`)         | HLS (HTTP) | MPEG‑DASH (HTTP) | RTSP |
|------------------------------------------|------------|------------------|------|
| HLS (`hls`) – `m3u8 + TS`                | ✔          | ✖                | ✖    |
| DASH (`dash`) – `mpd + fMP4`             | ✖          | ✔                | ✖    |
| TS (`ts`) – MPEG‑TS segments             | ✖          | ✖                | ✔*   |
| CMAF (`cmaf`) – CMAF fMP4 segments       | ✔ (HLS에서 사용 가능) | ✔ (DASH에서 사용 가능) | ✖ |

`*` TS 포맷은 이 프로젝트에서 내부적으로 HLS 파이프라인을 사용하지만, 주 사용 목적은 RTSP(MPEG‑TS over RTSP) 조합입니다.

### RTSP 재생 예시

- **기본 RTSP 포트**: `8554` (환경 변수 `RTSP_PORT`로 변경 가능)
- 업로드 시 `streaming_protocol=rtsp` 로 요청하면, 내부적으로 FFmpeg RTSP 서버가 해당 스트림 ID로 실행됩니다.

#### RTSP URL 예시

- 로컬 서버 기준:
  - `rtsp://localhost:8554/<stream_id>`
  - 예: `rtsp://localhost:8554/1`
- 원격 서버 예시 (`192.168.0.10`):
  - `rtsp://192.168.0.10:8554/<stream_id>`

`stream_id`는 업로드/변환 작업에 매핑된 값이며, RTSP 스트림을 생성한 뒤 `/api/v1/stream/{task_id}` 응답의 `rtsp_url` 필드에서 확인할 수 있습니다.

#### VLC에서 재생하는 방법

1. VLC 실행
2. 메뉴에서 **Media → Open Network Stream...** 선택
3. "Network URL" 입력 필드에 RTSP URL 입력 (예: `rtsp://localhost:8554/1`)
4. **Play** 클릭 → RTSP 스트림 재생

## Docker 설정

Docker 설정은 다음과 같습니다.

- **Ports**:
  - `8000`: 웹 UI 및 API
  - `8554`: RTSP 스트리밍 포트

- **Volumes**:
  - `./uploads`: 업로드된 비디오 파일
  - `./static/output`: 패키징/트랜스코딩된 출력 파일

- **Environment Variables**:
  - `UPLOAD_DIR`: 업로드 파일 디렉터리 (기본값: `/app/uploads`)
  - `OUTPUT_DIR`: 처리된 파일 디렉터리 (기본값: `/app/static/output`)
  - `RTSP_PORT`: RTSP 스트리밍 포트 (기본값: `8554`)

## FFmpeg 명령 설명

이 프로젝트는 `services/video_converter.py` 에서 FFmpeg를 사용해 업로드된 파일을 HLS, DASH, RTSP 스트림으로 변환합니다. 주요 명령과 옵션은 다음과 같습니다.

### HLS 변환 (`_convert_to_hls`)

개념적인 명령 구조:

```bash
ffmpeg -y -i <input> \
  -c:v libx264 -preset veryfast -crf <crf> [ -vf scale=... ] \
  -c:a aac \
  -hls_time <segment_duration> \
  -hls_playlist_type vod \
  -hls_segment_filename playlist_%03d.ts \
  -hls_flags independent_segments \
  -start_number 0 \
  <output>.m3u8
```

- `-y`: 기존 출력 파일을 확인 없이 덮어쓰기
- `-c:v libx264`: 비디오를 H.264(AVC)로 재인코딩
- `-preset veryfast`: 인코딩 속도/압축 효율 트레이드오프 (개발/테스트에서는 빠른 프리셋 사용)
- `-crf <value>`: H.264 화질 제어 (값이 낮을수록 고화질/고용량, 일반적인 범위 18–24)
- `-vf scale=...`: `resolution` 설정에 따라 해상도 조정 (예: 360p/720p/1080p)
- `-c:a aac`: 오디오를 AAC로 인코딩
- `-hls_time`: 세그먼트 길이(초). 예: 6이면 약 6초 단위 TS 세그먼트 생성
- `-hls_playlist_type vod`: VOD 스타일 HLS 플레이리스트
- `-hls_segment_filename`: 세그먼트 파일 이름 패턴 (예: `playlist_000.ts`)
- `-hls_flags independent_segments`: 세그먼트 경계를 독립 GOP에 맞춰 시킹/전환 안정화
- `-start_number 0`: 세그먼트 번호를 0부터 시작

### DASH 변환 (`_convert_to_dash`)

개념적인 명령 구조:

```bash
ffmpeg -y -i <input> \
  -map 0:v:0 -map 0:a:0 \
  -c:v libx264 -preset veryfast -crf <crf> [ -vf scale=... ] \
  -c:a aac \
  -f dash \
  -use_timeline 1 -use_template 1 \
  -seg_duration <segment_duration> \
  -frag_duration <segment_duration> \
  -window_size 5 \
  -adaptation_sets "id=0,streams=v id=1,streams=a" \
  -init_seg_name "init-stream$RepresentationID$.$ext$" \
  -media_seg_name "chunk-stream$RepresentationID$-$Number%05d$.$ext$" \
  <output>.mpd
```

- `-map 0:v:0 -map 0:a:0`: 입력의 첫 번째 비디오/오디오 트랙을 명시적으로 선택
- `-c:v libx264`, `-preset`, `-crf`, `-vf`, `-c:a aac`: HLS와 동일한 인코딩 설정
- `-f dash`: MPEG‑DASH (MPD + fMP4 세그먼트) 출력
- `-use_timeline 1`, `-use_template 1`: MPD에서 timeline, template addressing 사용
- `-seg_duration`, `-frag_duration`: 세그먼트/프래그먼트 길이(초)
- `-window_size 5`: 슬라이딩 윈도우 크기 (라이브 환경에 더 유용하지만 VOD에도 사용 가능)
- `-adaptation_sets`: 비디오/오디오를 별도 AdaptationSet으로 정의
- `-init_seg_name`, `-media_seg_name`: init/미디어 세그먼트 파일 이름 패턴

### RTSP 스트리밍 (`_start_rtsp_stream`)

개념적인 명령 구조:

```bash
ffmpeg -re -stream_loop -1 -i <input> \
  -c:v libx264 -preset veryfast -tune zerolatency \
  -f rtsp rtsp://0.0.0.0:<RTSP_PORT>/<stream_id>
```

- `-re`: 입력을 원래 프레임 레이트에 맞춰 읽어 실시간에 가깝게 재생
- `-stream_loop -1`: 입력 파일을 무한 반복 (데모/테스트용)
- `-c:v libx264 -preset veryfast`: 실시간 H.264 인코딩
- `-tune zerolatency`: 버퍼를 최소화해 지연 감소
- `-f rtsp`: RTSP 프로토콜로 출력
- `rtsp://0.0.0.0:<port>/<stream_id>`: 컨테이너 내부의 모든 인터페이스(0.0.0.0)에 RTSP 서버 바인딩

위 설정들은 데모/개발 환경에 맞춰진 값입니다. 실제 서비스 환경에서는 다음과 같이 조정할 수 있습니다.

- `crf`, `preset`, `resolution`을 조정해 화질/비트레이트/CPU 사용량을 튜닝
- HLS/DASH용으로 다중 해상도/비트레이트(ABR)를 구성하기 위해 추가 `-map`, `scale`, (HLS의 경우) `-var_stream_map` 등을 사용하는 확장

## 프로젝트 구조

- `main.py`: FastAPI 애플리케이션 및 엔드포인트 진입점
- `templates/`: HTML 템플릿
  - `index.html`: 메인 웹 UI
- `static/`: 정적 파일 (CSS, JS, 출력 비디오)
- `uploads/`: 업로드된 원본 비디오 파일

## 라이선스

MIT
