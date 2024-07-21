from pydantic import BaseModel

from src.tvdb.generated_models import (
    Links,
    MovieBaseRecord,
    MovieExtendedRecord,
    SearchResult,
    SeriesBaseRecord,
    SeriesExtendedRecord,
)


class _Response(BaseModel):
    """Model for any response of the TVDB API."""

    status: str


class _PaginatedResponse(_Response):
    links: Links


class SearchResponse(_PaginatedResponse):
    """Model for the response of the search endpoint of the TVDB API."""

    data: list[SearchResult]


class SeriesResponse(_Response):
    """Model for the response of the series/{id} endpoint of the TVDB API."""

    data: SeriesBaseRecord


class MovieResponse(_Response):
    """Model for the response of the movies/{id} endpoint of the TVDB API."""

    data: MovieBaseRecord


class SeriesExtendedResponse(_Response):
    """Model for the response of the series/{id}/extended endpoint of the TVDB API."""

    data: SeriesExtendedRecord


class MovieExtendedResponse(_Response):
    """Model for the response of the movies/{id}/extended endpoint of the TVDB API."""

    data: MovieExtendedRecord


type SearchResults = list[SearchResult]
