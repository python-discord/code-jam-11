from abc import ABC, abstractmethod
from typing import Any, ClassVar, Literal, overload, override

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
from src.tvdb.models import MovieResponse, SearchResponse, SeriesResponse
from src.utils.log import get_logger

log = get_logger(__name__)

type JSON_DATA = dict[str, JSON_DATA] | list[JSON_DATA] | str | int | float | bool | None  # noice


class _Media(ABC):
    def __init__(self, client: "TvdbClient"):
        self.client = client
        self._id: int | None = None

    @property
    def id(self) -> int | str | None:
        return self._id

    @id.setter
    def id(self, value: int | str) -> None:
        self._id = int(str(value).split("-")[1])

    def __call__(self, media_id: str) -> "_Media":
        self.id = media_id
        return self

    @abstractmethod
    async def search(self, search_query: str, limit: int = 1) -> list[Any]: ...

    @abstractmethod
    async def fetch(self, *, extended: bool = False) -> Any: ...


class Series(_Media):
    """Class to interact with the TVDB API for series."""

    @override
    async def search(self, search_query: str, limit: int = 1) -> list[SearchResult]:
        """Search for a series in the TVDB database.

        :param search_query:
        :param limit:
        :return:
        """
        return await self.client.search(search_query, "series", limit)

    @overload
    async def fetch(self, *, extended: Literal[False]) -> SeriesBaseRecord: ...

    @overload
    async def fetch(self, *, extended: Literal[True]) -> SeriesExtendedRecord: ...

    @override
    async def fetch(self, *, extended: bool = False) -> SeriesBaseRecord | SeriesExtendedRecord:
        """Fetch a series by its ID.

        :param extended:
        :return:
        """
        data = await self.client.request("GET", f"series/{self.id}" + ("/extended" if extended else ""))
        return SeriesResponse(**data).data  # pyright: ignore[reportCallIssue]


class Movies(_Media):
    """Class to interact with the TVDB API for movies."""

    @override
    async def search(self, search_query: str, limit: int = 1) -> list[SearchResult]:
        """Search for a movie in the TVDB database.

        :param search_query:
        :param limit:
        :return: list[SearchResult]
        """
        return await self.client.search(search_query, "movie", limit)

    @overload
    async def fetch(self, *, extended: Literal[False]) -> MovieBaseRecord: ...
    @overload
    async def fetch(self, *, extended: Literal[True]) -> MovieExtendedRecord: ...
    @override
    async def fetch(self, *, extended: bool = False) -> MovieBaseRecord | MovieExtendedRecord:
        """Fetch a movie by its ID.

        :param extended:  Whether to fetch extended information.
        :return:
        """
        data = await self.client.request("GET", f"movies/{self.id}" + ("/extended" if extended else ""))
        return MovieResponse(**data).data  # pyright: ignore[reportCallIssue]


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
        self.series = Series(self)
        self.movies = Movies(self)

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
    ) -> list[SearchResult]:
        """Search for a series or movie in the TVDB database."""
        query: dict[str, str] = {"query": search_query, "limit": str(limit)}
        if entity_type != "all":
            query["type"] = entity_type
        data = await self.request("GET", "search", query=query)
        response = SearchResponse(**data)  # pyright: ignore[reportCallIssue]
        return response.data

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
