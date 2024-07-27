from pathlib import Path

from src.utils.config import get_config

GITHUB_REPO = "https://github.com/ItsDrike/code-jam-2024"
BOT_TOKEN = get_config("BOT_TOKEN")
TVDB_API_KEY = get_config("TVDB_API_KEY")

SQLITE_DATABASE_FILE = get_config("SQLITE_DATABASE_FILE", cast=Path, default=Path("./database.db"))
ECHO_SQL = get_config("ECHO_SQL", cast=bool, default=False)
DB_ALWAYS_MIGRATE = get_config("DB_ALWAYS_MIGRATE", cast=bool, default=False)

FAIL_EMOJI = "❌"
SUCCESS_EMOJI = "✅"
GROUP_EMOJI = get_config("GROUP_EMOJI", default=":file_folder:")
COMMAND_EMOJI = get_config("COMMAND_EMOJI", default=":arrow_forward:")

THETVDB_COPYRIGHT_FOOTER = (
    "Metadata provided by TheTVDB. Please consider adding missing information or subscribing at " "thetvdb.com."
)
THETVDB_LOGO = "https://www.thetvdb.com/images/attribution/logo1.png"

# The default rate-limit might be a bit too small for production-ready bots that live
# on multiple guilds. But it's good enough for our demonstration purposes and it's
# still actually quite hard to hit this rate-limit on a single guild, unless multiple
# people actually try to make many requests after each other..
#
# Note that tvdb doesn't actually have rate-limits (or at least they aren't documented),
# but we should still be careful not to spam the API too much and be on the safe side.
TVDB_RATE_LIMIT_REQUESTS = get_config("TVDB_RATE_LIMIT_REQUESTS", cast=int, default=5)
TVDB_RATE_LIMIT_PERIOD = get_config("TVDB_RATE_LIMIT_PERIOD", cast=float, default=5)  # seconds
