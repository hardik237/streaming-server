FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 python3-pip python3-gi python3-dev \
    gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav \
    gstreamer1.0-rtsp gstreamer1.0-x \
    gir1.2-gstreamer-1.0 gir1.2-gst-plugins-base-1.0 \
    ffmpeg libopencv-dev python3-opencv \
    wget curl git build-essential \
    libgirepository1.0-dev libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install MediaMTX
RUN wget https://github.com/bluenviron/mediamtx/releases/download/v1.15.3/mediamtx_v1.15.3_linux_amd64.tar.gz \
    && tar -xzf mediamtx_v1.15.3_linux_amd64.tar.gz \
    && mv mediamtx /usr/local/bin/ \
    && rm mediamtx_v1.15.3_linux_amd64.tar.gz

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make start script executable
RUN chmod +x start.sh

EXPOSE 5000 1935 8554 8888 8889 9997

CMD ["./start.sh"]
