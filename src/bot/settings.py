import os
from pathlib import Path

from dotenv import load_dotenv

dotenv_path = Path(Path(__file__).parent) / "../../.env"
load_dotenv(dotenv_path)
db_path = Path(__file__).parent / "db/"
test_db_path = Path(__file__).parent / "db/test"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GUILD_ID = os.environ.get("GUILD_ID")
GIF_CHANNEL_ID = os.environ.get("GIF_CHANNEL_ID")

BOT_TOKEN_ARRAY = os.environ.get("TOKEN_ARRAY")
