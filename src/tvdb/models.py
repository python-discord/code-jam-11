from pydantic import BaseModel

from src.tvdb.generated_models import Links, SearchResult, SeriesBaseRecord, SeriesExtendedRecord


class Response(BaseModel):
    """Model for any response of the TVDB API."""

    status: str


class PaginatedResponse(Response):
    """Model for the response of the search endpoint of the TVDB API."""

    links: Links


class SearchResponse(PaginatedResponse):
    """Model for the response of the search endpoint of the TVDB API."""

    data: list[SearchResult]


class SeriesResponse(Response):
    """Model for the response of the series/{id} endpoint of the TVDB API."""

    data: SeriesBaseRecord


class SeriesExtendedResponse(Response):
    """Model for the response of the series/{id}/extended endpoint of the TVDB API."""

    data: SeriesExtendedRecord
    episodes: list[dict[str, str]]
