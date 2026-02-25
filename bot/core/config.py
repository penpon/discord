import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "messages.db")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")

ADMIN_USER_ID = os.environ.get("ADMIN_USER_ID", "514786727634927647")

URL_PATTERN = re.compile(r"\bhttps?://\S+")
LONG_NUMBER_PATTERN = re.compile(r"\b\d{5,}\b")
