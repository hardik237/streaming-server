# Live Video Streaming Solution

Implementation for live video streaming

## Architecture

- **UI**: Streamlit frontend for source selection, live view, controls
- **Streaming**: MediaMTX for multi-protocol streaming (RTMP/HLS/WebRTC)
- **Pipeline**: GStreamer for video processing
- **AI**: Ultralytics YOLOv8 for real-time object detection
- **Database**: MongoDB for maintaining stream metadata
- **Deployment**: Docker Compose with 3 services

See `DESIGN.md` for complete architecture documentation.

## Quick Start

### Prerequisites

- Docker & Docker Compose

### Setup

1. Start Server:
- This will pull necessary images and start all containers in detached mode.
```bash
./start_server.sh
```

   
2. Open UI Dashboard:
```bash

http://<system-ip-address>:8501
```

3. Stop Server:
```bash
./stop_server.sh
```
 

### Services

- **streaming-ui**: http://localhost:8501 (Streamlit)
- **streaming-service**: http://localhost:5000 (Flask REST Server)
   - **MediaMTX**:
     - RTMP: rtmp://localhost:1935
     - HLS: http://localhost:8888
     - WebRTC: http://localhost:8889
     - API: http://localhost:9997
     - Playback: http://localhost:9996
- **streaming-mongo**: mongodb://localhost:27017 (Mongo database)
- **mediamtx-rtsp-server**: http://localhost:9554 (Dummy RTSP Server for local testing)

## Usage

1. **Select Source**: Choose webcam or enter RTSP URL
2. **Create Stream**: Click to start streaming
3. **Live View**: WebRTC player with low-latency feed
4. **Playback**: View recordings in HLS player

## Project Structure

```
streaming-server/
├── DESIGN.md                    # Complete architecture documentation
├── docker-compose.yml           # Container orchestration
├── README.md                    # This file
├── ui/                          # Streamlit UI service
│   ├── Dockerfile
│   ├── build_docker.sh
│   ├── start.sh                 # Startup script
│   ├── requirements.txt
│   ├── live.py                  # Index page (source selection)
│   ├── pages/
│   │   └── playback.py          # Playback page (HLS viewer)
│   └── utils/
│       ├── db.py                # MongoDB client
│       └── api_client.py        # REST client for streaming-service
│       └── utils.py             # Helper functions
├── streaming/                   # Streaming service
│   ├── Dockerfile
│   ├── build_docker.sh
│   ├── requirements.txt
│   ├── start.sh                 # Startup script (MediaMTX + Flask)
│   ├── app.py                   # Flask REST API
│   ├── pipeline.py              # GStreamer pipeline controller
│   ├── ai_processor.py          # Ultralytics YOLOv8 AI processing
│   ├── mediamtx.yml             # MediaMTX configuration
│   ├── mediamtx_client.py       # MediaMTX API client
│   └── utils/
│       └── db.py                # MongoDB client
│       └── utils.py             # Helper functions
└── recordings/                  # Volume for recordings
```

## Features

- Live video streaming with WebRTC
- RTSP and webcam sources
- Recording with HLS playback
- MongoDB persistence
- Docker containerization

## Known Limitations


## Future Enhancements

- Object-based search in recordings

## License

Open source components are used under their respective licenses.
