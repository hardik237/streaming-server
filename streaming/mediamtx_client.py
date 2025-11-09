"""
MediaMTX API client
Interacts with MediaMTX REST API for stream management
"""
import requests
import logging

logger = logging.getLogger(__name__)

class MediaMTXClient:
    """Client for MediaMTX API"""
    
    def __init__(self, api_url="http://localhost:9997"):
        self.api_url = api_url
        self.session = requests.Session()
    
    def get_paths(self):
        """Get all active paths/streams"""
        try:
            response = self.session.get(f"{self.api_url}/v3/paths/list")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting paths: {e}")
            return None
    
    def get_path_info(self, path_name):
        """Get info for a specific path"""
        try:
            response = self.session.get(f"{self.api_url}/v3/paths/get/{path_name}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting path info: {e}")
            return None
    
    def get_all_recordings(self):
        """Get all recordings"""
        try:
            response = self.session.get(f"{self.api_url}/v3/recordings/list/")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting recordings: {e}")
            return None
    
    def get_path_recordings(self, path_name):
        """Get recordings for a specific path"""
        try:
            response = self.session.get(f"{self.api_url}/v3/recordings/get/{path_name}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting recordings: {e}")
            return None
    
    
