from abc import ABC, abstractmethod
from typing import ClassVar, Literal, overload, override

import aiohttp
from yarl import URL

from src.settings import TVDB_API_KEY
from src.tvdb.generated_models import (
    MovieBaseRecord,
    MovieExtendedRecord,
    SearchResult,
    SeriesBaseRecord,
    SeriesExtendedRecord,
)
from src.tvdb.models import (
    MovieExtendedResponse,
    MovieResponse,
    SearchResponse,
    SeriesExtendedResponse,
    SeriesResponse,
)
from src.utils.log import get_logger

log = get_logger(__name__)

type JSON_DATA = dict[str, JSON_DATA] | list[JSON_DATA] | str | int | float | bool | None  # noice

type SeriesRecord = SeriesBaseRecord | SeriesExtendedRecord
type MovieRecord = MovieBaseRecord | MovieExtendedRecord
type AnyRecord = SeriesRecord | MovieRecord


def parse_media_id(media_id: int | str) -> int:
    """Parse the media ID from a string."""
    return int(str(media_id).removeprefix("movie-").removeprefix("series-"))


class _Media(ABC):
    def __init__(self, client: "TvdbClient", data: SeriesRecord | MovieRecord | SearchResult):
        self.data = data
        self.client = client
        self.name: str | None = self.data.name
        self.overview: str | None = None
        # if the class name is "Movie" or "Series"
        self.entity_type: Literal["Movie", "Series"] = self.__class__.__name__  # pyright: ignore [reportAttributeAccessIssue]
        if hasattr(self.data, "overview"):
            self.overview = self.data.overview  # pyright: ignore [reportAttributeAccessIssue]
        self.slug: str | None = None
        if hasattr(self.data, "slug"):
            self.slug = self.data.slug
        if hasattr(self.data, "id"):
            self.id = self.data.id

        self.name_eng: str | None = None
        self.overview_eng: str | None = None

        self.image_url: URL | None = None
        if isinstance(self.data, SearchResult) and self.data.image_url:
            self.image_url = URL(self.data.image_url)
        elif not isinstance(self.data, SearchResult) and self.data.image:
            self.image_url = URL(self.data.image)

        if isinstance(self.data, SearchResult):
            if self.data.translations and self.data.translations.root:
                self.name_eng = self.data.translations.root.get("eng")
            if self.data.overviews and self.data.overviews.root:
                self.overview_eng = self.data.overviews.root.get("eng")
        else:
            if self.data.aliases:
                self.name_eng = next(alias for alias in self.data.aliases if alias.language == "eng").name
            if isinstance(self.data, (SeriesExtendedRecord, MovieExtendedRecord)) and self.data.translations:
                if self.data.translations.name_translations:
                    self.name_eng = next(
                        translation.name
                        for translation in self.data.translations.name_translations
                        if translation.language == "eng"
                    )
                if self.data.translations.overview_translations:
                    self.overview_eng = next(
                        translation.overview
                        for translation in self.data.translations.overview_translations
                        if translation.language == "eng"
                    )

    @property
    def bilingual_name(self) -> str | None:
        if self.name == self.name_eng:
            return self.name
        return f"{self.name} ({self.name_eng})"

    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int | str) -> None:  # pyright: ignore[reportPropertyTypeMismatch]
        self._id = parse_media_id(value)

    @classmethod
    @abstractmethod
    async def fetch(cls, media_id: int | str, *, client: "TvdbClient", extended: bool = False) -> "_Media": ...


class Movie(_Media):
    """Class to interact with the TVDB API for movies."""

    @overload
    @classmethod
    async def fetch(cls, media_id: int | str, client: "TvdbClient", *, extended: Literal[False]) -> "Movie": ...
    @overload
    @classmethod
    async def fetch(cls, media_id: int | str, client: "TvdbClient", *, extended: Literal[True]) -> "Movie": ...

    @override
    @classmethod
    async def fetch(cls, media_id: int | str, client: "TvdbClient", *, extended: bool = False) -> "Movie":
        """Fetch a movie by its ID.

        :param media_id:  The ID of the movie.
        :param client:  The TVDB client to use.
        :param extended:  Whether to fetch extended information.
        :return:
        """
        media_id = parse_media_id(media_id)
        response = await client.request("GET", f"movies/{media_id}" + ("/extended" if extended else ""))
        response = MovieResponse(**response) if not extended else MovieExtendedResponse(**response)  # pyright: ignore[reportCallIssue]
        return cls(client, response.data)


class Series(_Media):
    """Class to interact with the TVDB API for series."""

    @overload
    @classmethod
    async def fetch(cls, media_id: int | str, client: "TvdbClient", *, extended: Literal[False]) -> "Series": ...
    @overload
    @classmethod
    async def fetch(cls, media_id: int | str, client: "TvdbClient", *, extended: Literal[True]) -> "Series": ...

    @override
    @classmethod
    async def fetch(cls, media_id: int | str, client: "TvdbClient", *, extended: bool = False) -> "Series":
        """Fetch a series by its ID.

        :param media_id:  The ID of the series.
        :param client:  The TVDB client to use.
        :param extended:  Whether to fetch extended information.
        :return:
        """
        media_id = parse_media_id(media_id)
        response = await client.request("GET", f"series/{media_id}" + ("/extended" if extended else ""))
        response = SeriesResponse(**response) if not extended else SeriesExtendedResponse(**response)  # pyright: ignore[reportCallIssue]
        return cls(client, response.data)


class InvalidApiKeyError(Exception):
    """Exception raised when the TVDB API key used was invalid."""

    def __init__(self, response: aiohttp.ClientResponse, response_txt: str):
        self.response = response
        self.response_txt = response_txt
        super().__init__("Invalid TVDB API key.")


class TvdbClient:
    """Class to interact with the TVDB API."""

    BASE_URL: ClassVar[URL] = URL("https://api4.thetvdb.com/v4/")

    def __init__(self, http_session: aiohttp.ClientSession):
        self.http_session = http_session
        self.auth_token = None

    @overload
    async def request(
        self,
        method: Literal["GET"],
        endpoint: str,
        body: None = None,
        query: dict[str, str] | None = None,
    ) -> JSON_DATA: ...

    @overload
    async def request(
        self, method: Literal["POST"], endpoint: str, body: JSON_DATA, query: None = None
    ) -> JSON_DATA: ...

    async def request(
        self,
        method: Literal["GET", "POST"],
        endpoint: str,
        body: JSON_DATA = None,
        query: dict[str, str] | None = None,
    ) -> JSON_DATA:
        """Make an authorized request to the TVDB API."""
        log.trace(f"Making TVDB {method} request to {endpoint}")

        if self.auth_token is None:
            log.trace("No auth token found, requesting initial login.")
            await self._login()
        headers = {"Authorization": f"Bearer {self.auth_token}", "Accept": "application/json"}

        url = self.BASE_URL / endpoint.removeprefix("/")
        if method == "GET" and query:
            url = url.with_query(query)
        async with self.http_session.request(method, url, headers=headers, json=body) as response:
            if response.status == 401:
                log.debug("TVDB API token expired, requesting new token.")
                self.auth_token = None
                # TODO: might be an infinite loop
                return await self.request(method, endpoint, body)  # pyright: ignore[reportCallIssue,reportArgumentType]
            response.raise_for_status()
            return await response.json()

    async def search(
        self, search_query: str, entity_type: Literal["series", "movie", "all"] = "all", limit: int = 1
    ) -> list[Movie | Series]:
        """Search for a series or movie in the TVDB database."""
        query: dict[str, str] = {"query": search_query, "limit": str(limit)}
        if entity_type != "all":
            query["type"] = entity_type
        data = await self.request("GET", "search", query=query)
        response = SearchResponse(**data)  # pyright: ignore[reportCallIssue]
        return [Movie(self, result) if result.id[0] == "m" else Series(self, result) for result in response.data]

    async def _login(self) -> None:
        """Obtain the auth token from the TVDB API.

        This token has one month of validity.
        """
        log.debug("Requesting TVDB API login")
        url = self.BASE_URL / "login"
        async with self.http_session.post(url, json={"apikey": TVDB_API_KEY}) as response:
            if response.status == 401:
                log.error("Invalid TVDB API key, login request failed.")
                response_txt = await response.text()
                raise InvalidApiKeyError(response, response_txt)

            response.raise_for_status()
            data = await response.json()
            self.auth_token = data["data"]["token"]
