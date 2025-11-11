import os
from pathlib import Path
from dotenv import load_dotenv

# load .env from project root if present
root = Path(__file__).resolve().parents[1]
load_dotenv(root / '.env')

API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://mongo:27017')
DEFAULT_GOFILE_TOKEN = os.getenv('DEFAULT_GOFILE_TOKEN', '')
DEFAULT_PIXELDRAIN_KEY = os.getenv('DEFAULT_PIXELDRAIN_KEY', '')

# optional runtime settings
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 0))  # 0 means no limit
