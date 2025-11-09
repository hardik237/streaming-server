import utils.db

db = utils.db.get_db()

def check_stream_exists(stream_id):
    """Check if a stream with the given stream_id exists in the database"""
    return db.streams.find_one({"stream_id": stream_id}) is not None