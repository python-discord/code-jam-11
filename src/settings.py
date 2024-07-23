from pathlib import Path

from src.utils.config import get_config

GITHUB_REPO = "https://github.com/ItsDrike/code-jam-2024"
BOT_TOKEN = get_config("BOT_TOKEN")
TVDB_API_KEY = get_config("TVDB_API_KEY")

SQLITE_DATABASE_FILE = get_config("SQLITE_DATABASE_FILE", cast=Path, default=Path("./database.db"))
ECHO_SQL = get_config("ECHO_SQL", cast=bool, default=False)

FAIL_EMOJI = "❌"
SUCCESS_EMOJI = "✅"
GROUP_EMOJI = get_config("GROUP_EMOJI", default=":file_folder:")
COMMAND_EMOJI = get_config("COMMAND_EMOJI", default=":arrow_forward:")

THETVDB_COPYRIGHT_FOOTER = (
    "Metadata provided by TheTVDB. Please consider adding missing information or subscribing at " "thetvdb.com."
)
THETVDB_LOGO = "https://www.thetvdb.com/images/attribution/logo1.png"
