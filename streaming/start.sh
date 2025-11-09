#!/bin/bash

# Start MediaMTX in background
pkill -f mediamtx
echo "Starting MediaMTX..."
mediamtx mediamtx.yml &

# Wait for MediaMTX to start
sleep 3

# Start Flask API
echo "Starting Flask API..."
python3 app.py
