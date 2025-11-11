from pymongo import MongoClient
from config import MONGODB_URL

client = MongoClient(MONGODB_URL)
db = client['leechbot']
users = db['users']


def get_user(user_id: int) -> dict:
    doc = users.find_one({'user_id': user_id})
    if not doc:
        doc = {'user_id': user_id, 'gofile_token': None, 'pixeldrain_key': None}
        users.insert_one(doc)
    return doc


def set_user_token(user_id: int, kind: str, token: str | None):
    users.update_one({'user_id': user_id}, {'$set': {kind: token}}, upsert=True)
