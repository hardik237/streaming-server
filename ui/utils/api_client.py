"""
API client for communicating with streaming-service
"""
import requests
import os

STREAMING_SERVICE_URL = os.getenv("STREAMING_SERVICE_URL", "http://localhost:5000")

def create_stream(stream_id, source_type, source):
    """Create a new stream"""
    try:
        print("Creating stream via API client...")
        response = requests.post(
            f"{STREAMING_SERVICE_URL}/internal/streams/start",
            json={
                "stream_id": stream_id,
                "type": source_type,
                "source": source,
            },
            timeout=10
        )
        # response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "status": "error"}

def stop_stream(stream_id):
    """Stop a stream"""
    try:
        print(f"Stopping stream {stream_id} via API client...")
        response = requests.post(
            f"{STREAMING_SERVICE_URL}/internal/streams/stop",
            json={"stream_id": stream_id},
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}
    
def restart_stream(stream_id):
    """Restart a stream"""
    try:
        print(f"Restarting stream {stream_id} via API client...")
        response = requests.post(
            f"{STREAMING_SERVICE_URL}/internal/streams/restart",
            json={"stream_id": stream_id},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}
    
def delete_stream(stream_id):
    """Delete a stream"""
    try:
        print(f"Deleting stream {stream_id} via API client...")
        response = requests.post(
            f"{STREAMING_SERVICE_URL}/internal/streams/delete",
            json={"stream_id": stream_id},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def stop_all_streams():
    """Stop all streams"""
    try:
        print("Stopping all streams via API client...")
        response = requests.post(
            f"{STREAMING_SERVICE_URL}/internal/streams/stop_all",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_all_streams():
    """Get all active streams"""
    try:
        print("Getting all streams via API client...")
        response = requests.get(
            f"{STREAMING_SERVICE_URL}/internal/streams/get_all_streams",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_recordings(stream_id, start_time=None, end_time=None):
    """Get recordings for a specific stream"""
    try:
        print(f"Getting recordings for stream {stream_id} via API client...")
        print(f"### start_time={start_time}, end_time={end_time}")
        response = requests.get(
            f"{STREAMING_SERVICE_URL}/internal/streams/get_recordings",
            params={"stream_id": stream_id, "start_time": start_time, "end_time": end_time},
            timeout=10
        )
        print("Get Recordings Response:", response.text)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}
    
def flush_db():
    """Flush the database (for testing purposes)"""
    try:
        print("Stopping all streams before flushing database via API client...")
        # Stop all streams first
        stop_all_streams()
        
        print("Flushing database via API client...")
        response = requests.post(
            f"{STREAMING_SERVICE_URL}/internal/streams/flush_db",
            timeout=10
        )
        print("Database flush response:", response.text)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


