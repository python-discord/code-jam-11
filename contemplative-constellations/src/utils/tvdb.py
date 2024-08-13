from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.tvdb.client import Episode


def by_season(episodes: list["Episode"]) -> dict[int, list["Episode"]]:
    """Group episodes by season."""
    seasons = {}
    for episode in episodes:
        seasons.setdefault(episode.season_number, []).append(episode)
    return seasons
