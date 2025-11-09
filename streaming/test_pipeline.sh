gst-launch-1.0 -e \
    v4l2src device=/dev/video0 ! \
    decodebin ! \
    videoconvert ! \
    video/x-raw,format=I420 ! \
    x264enc bitrate=2000 speed-preset=ultrafast tune=zerolatency ! \
    flvmux streamable=true ! \
    rtmpsink location=rtmp://localhost:1935/test