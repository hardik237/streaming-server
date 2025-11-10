"""
Flask REST API for streaming-service
The API server provides following endpoints:

- Health Check: /health
- Start Stream: /internal/streams/start
- Stop Stream: /internal/streams/stop
- Restart Stream: /internal/streams/restart
- Delete Stream: /internal/streams/delete
- Stop All Streams: /internal/streams/stop_all
- Get All Streams: /internal/streams/get_all_streams
- Get Recordings: /internal/streams/get_recordings
- Flush Database: /internal/streams/flush_db

"""
from flask import Flask, request, jsonify
import os
import sys
import logging
from utils.db import get_db, ensure_indexes
import utils.utils as utils
from pipeline import PipelineController
from mediamtx_client import MediaMTXClient
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize components
db = get_db()
ensure_indexes(db)
pipeline_controller = PipelineController()
mediamtx_client = MediaMTXClient(os.getenv("MEDIAMTX_API", "http://localhost:9997"))

#--------------------------------------------------------------------------------

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "streaming-service"})

@app.route('/internal/streams/start', methods=['POST'])
def start_stream():
    """Start a new stream"""
    try:
        data = request.json
        stream_id = data.get('stream_id')
        source_type = data.get('type')  # 'webcam' or 'rtsp'
        source = data.get('source')
        ai_processing = data.get('ai_processing', False)
        
        if utils.check_stream_exists(stream_id):
            return jsonify({"error": "Stream ID already exists"}), 400
        
        if not all([stream_id, source_type, source]):
            return jsonify({"error": "Missing required fields"}), 400
        
        logger.info(f"Starting stream {stream_id}: {source_type} - {source}")
        
        # Create stream document
        webrtc_path = stream_id
        
        stream_doc = {
            "stream_id": stream_id,
            "source_type": source_type,
            "source_spec": {"device": source} if source_type == "webcam" else {"rtsp_url": source},
            "ai_processing": ai_processing,
            "status": "starting",
            "webrtc_path": webrtc_path,
            "created_at": db.current_time(),
            "updated_at": db.current_time()
        }
        
        db.streams.insert_one(stream_doc)
        
        # Start pipeline (passthrough mode initially)
        pipeline_controller.start_pipeline(
            stream_id=stream_id,
            source_type=source_type,
            source=source,
            webrtc_path=webrtc_path,
            ai_processing=ai_processing
        )
        
        # Update status
        db.streams.update_one(
            {"stream_id": stream_id},
            {"$set": {"status": "live", "updated_at": db.current_time()}}
        )
        
        return jsonify({
            "stream_id": stream_id,
            "webrtc_path": webrtc_path,
            "webrtc_url": f"http://localhost:8889/{webrtc_path}",
            "hls_url": f"http://localhost:8888/{webrtc_path}/index.m3u8",
            "status": "live"
        })
        
    except Exception as e:
        logger.error(f"Error starting stream: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/internal/streams/stop', methods=['POST'])
def stop_stream():
    """Stop a stream"""
    try:
        stream_id = request.json.get('stream_id')
        
        if not stream_id:
            return jsonify({"error": "stream_id required"}), 400
        
        logger.info(f"Stopping stream {stream_id}")
        
        # Stop pipeline
        pipeline_controller.stop_pipeline(stream_id)
        
        # Update database
        db.streams.update_one(
            {"stream_id": stream_id},
            {"$set": {"status": "stopped", "updated_at": db.current_time()}}
        )
        
        return jsonify({"status": "stopped", "stream_id": stream_id})
        
    except Exception as e:
        logger.error(f"Error stopping stream: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/internal/streams/restart', methods=['POST'])
def restart_stream():
    """Restart a stream"""
    try:
        stream_id = request.json.get('stream_id')

        logger.info(f"Received request to restart stream: {stream_id}")
        
        if not stream_id:
            return jsonify({"error": "stream_id required"}), 400
        
        stream = db.streams.find_one({"stream_id": stream_id})
        if not stream:
            return jsonify({"error": "Stream not found"}), 404
        
        if stream.get("status") == "live":
            return jsonify({"error": "Stream is already live"}), 400
        
        source_type = stream.get("source_type")
        source_spec = stream.get("source_spec", {})
        source = source_spec.get("device") if source_type == "webcam" else source_spec.get("rtsp_url")
        webrtc_path = stream.get("webrtc_path")
        ai_processing = stream.get("ai_processing", False)
        
        # Stop existing pipeline if any
        pipeline_controller.stop_pipeline(stream_id)
        
        # Start pipeline again
        pipeline_controller.start_pipeline(
            stream_id=stream_id,
            source_type=source_type,
            source=source,
            webrtc_path=webrtc_path,
            ai_processing=ai_processing
        )
        
        # Update status
        db.streams.update_one(
            {"stream_id": stream_id},
            {"$set": {"status": "live", "updated_at": db.current_time()}}
        )
        
        return jsonify({"status": "restarted", "stream_id": stream_id})
        
    except Exception as e:
        logger.error(f"Error restarting stream: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/internal/streams/delete', methods=['POST'])
def delete_stream():
    """Delete a stream"""
    try:
        stream_id = request.json.get('stream_id')
        
        if not stream_id:
            return jsonify({"error": "stream_id required"}), 400
        
        logger.info(f"Deleting stream {stream_id}")
        
        # Stop pipeline if running
        pipeline_controller.stop_pipeline(stream_id)
        
        # Remove from database
        db.streams.delete_one({"stream_id": stream_id})
        
        # delete recordings from storage
        recordings_path = f"/recordings/{stream_id}"
        if os.path.exists(recordings_path):
            os.system(f"rm -rf {recordings_path}")
            logger.info(f"Deleted recordings at {recordings_path}")
        
        return jsonify({"status": "deleted", "stream_id": stream_id})
        
    except Exception as e:
        logger.error(f"Error deleting stream: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/internal/streams/stop_all', methods=['POST'])
def stop_all_streams():
    """Stop all active streams"""
    try:
        logger.info("Stopping all active streams")
        
        active_streams = list(db.streams.find({"status": "live"}))
        for stream in active_streams:
            stream_id = stream["stream_id"]
            pipeline_controller.stop_pipeline(stream_id)
            db.streams.update_one(
                {"stream_id": stream_id},
                {"$set": {"status": "stopped", "updated_at": db.current_time()}}
            )
        
        return jsonify({"stopped_streams": [s["stream_id"] for s in active_streams]})
        
    except Exception as e:
        logger.error(f"Error stopping all streams: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/internal/streams/get_all_streams', methods=['GET'])
def get_all_streams():
    """Get all streams"""
    try:
        streams = list(db.streams.find())
        for stream in streams:
            stream['_id'] = str(stream['_id'])  # Convert ObjectId to string
        return jsonify(streams)
    except Exception as e:
        logger.error(f"Error fetching streams: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/internal/streams/get_recordings', methods=['GET'])
def get_recordings():
    """Get recordings for a specific stream/path"""
    try:
        stream_id = request.args.get('stream_id')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        
        logger.info(f"Received request to get recordings for stream: {stream_id}")
        
        if not stream_id:
            return jsonify({"error": "stream_id required"}), 400
                
        logger.info(f"Fetching recordings for stream {stream_id}")
        recordings = mediamtx_client.get_path_recordings(stream_id, start_time, end_time)
        print("Recordings fetched:", recordings)
        if recordings is None:
            return jsonify({"error": "Could not fetch recordings"}), 500
        
        return jsonify(recordings)
        
    except Exception as e:
        traceback = sys.exc_info()[2]
        logger.error(f"Error getting recordings for stream: {e} at line {traceback.tb_lineno}")
        return jsonify({"error": str(e)}), 500
    

@app.route('/internal/streams/flush_db', methods=['POST'])
def flush_db_endpoint():
    """Flush the database (for testing purposes)"""
    try:
        logger.info("Flushing the database")
        db.streams.drop()
        
        # delete all recordings from storage
        logger.info("Deleting all recordings from storage")
        os.system(f"rm -rf /recordings/*")
        
        return jsonify({"status": "database flushed"})
    except Exception as e:
        logger.error(f"Error flushing database: {e}")
        return jsonify({"error": str(e)}), 500

#--------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    

