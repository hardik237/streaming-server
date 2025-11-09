"""
MongoDB client for streaming-service
"""
import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

_client = None
_db = None

def get_db():
    """Get MongoDB database instance (singleton)"""
    global _client, _db
    
    if _db is None:
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        db_name = os.getenv('MONGODB_DB', 'video_streaming')
        
        logger.info(f"Connecting to MongoDB: {mongo_uri}")
        _client = MongoClient(mongo_uri)
        _db = _client[db_name]
        _db.current_time = lambda: datetime.utcnow()
        
    return _db

def ensure_indexes(db):
    """Create indexes on collections"""
    try:
        # Streams indexes
        db.streams.create_index([("stream_id", ASCENDING)], unique=True)
        db.streams.create_index([("status", ASCENDING)])
        db.streams.create_index([("created_at", DESCENDING)])
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

