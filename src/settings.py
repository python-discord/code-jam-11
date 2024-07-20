import os
from pathlib import Path

from dotenv import load_dotenv

dotenv_path = Path(Path(__file__).parent) / "../.env"
load_dotenv(dotenv_path)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GUILD_ID = os.environ.get("GUILD_ID")
