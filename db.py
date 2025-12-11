from pymongo import MongoClient
from config import MONGODB_URL

client = MongoClient(MONGODB_URL)
db = client['leechbot']
users = db['users']


def get_user(user_id: int) -> dict:
    """Get user data from database, create if doesn't exist."""
    doc = users.find_one({'user_id': user_id})
    if not doc:
        doc = {'user_id': user_id, 'gofile_token': None, 'pixeldrain_key': None}
        users.insert_one(doc)
    return doc


def set_user_token(user_id: int, kind: str, token: str | None):
    """Set user token (gofile_token or pixeldrain_key)."""
    users.update_one({'user_id': user_id}, {'$set': {kind: token}}, upsert=True)
