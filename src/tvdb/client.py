from abc import ABC, abstractmethod
from enum import Enum
from typing import ClassVar, Literal, Self, final, overload, override

import aiohttp
from yarl import URL

from src.settings import TVDB_API_KEY
from src.tvdb.generated_models import (
    MovieBaseRecord,
    MovieExtendedRecord,
    MoviesIdExtendedGetResponse,
    MoviesIdGetResponse,
    SearchGetResponse,
    SearchResult,
    SeriesBaseRecord,
    SeriesExtendedRecord,
    SeriesIdExtendedGetResponse,
    SeriesIdGetResponse,
)
from src.utils.log import get_logger

from .errors import BadCallError, InvalidApiKeyError, InvalidIdError

log = get_logger(__name__)

type JSON_DATA = dict[str, JSON_DATA] | list[JSON_DATA] | str | int | float | bool | None  # noice

type SeriesRecord = SeriesBaseRecord | SeriesExtendedRecord
type MovieRecord = MovieBaseRecord | MovieExtendedRecord
type AnyRecord = SeriesRecord | MovieRecord


class FetchMeta(Enum):
    """When calling fetch with extended=True, this is used if we want to fetch translations or episodes as well."""

    TRANSLATIONS = "translations"
    EPISODES = "episodes"


def parse_media_id(media_id: int | str) -> int:
    """Parse the media ID from a string."""
    try:
        media_id = int(str(media_id).removeprefix("movie-").removeprefix("series-"))
    except ValueError:
        raise InvalidIdError("Invalid media ID.")
    else:
        return media_id


class _Media(ABC):
    ENDPOINT: ClassVar[str]

    ResponseType: ClassVar[type[MoviesIdGetResponse | SeriesIdGetResponse]]
    ExtendedResponseType: ClassVar[type[MoviesIdExtendedGetResponse | SeriesIdExtendedGetResponse]]

    def __init__(self, client: "TvdbClient", data: AnyRecord | SearchResult | None):
        if data is None:
            raise ValueError("Data can't be None but is allowed to because of the broken pydantic generated models.")
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
    def supports_meta(cls, meta: FetchMeta) -> bool:
        """Check if the class supports a specific meta."""
        ...

    @classmethod
    async def fetch(
        cls,
        media_id: int | str,
        client: "TvdbClient",
        *,
        extended: bool = False,
        short: bool = True,
        meta: FetchMeta | None = None,
    ) -> Self:
        """Fetch a movie by its ID.

        :param media_id:  The ID of the movie.
        :param client:  The TVDB client to use.
        :param extended:  Whether to fetch extended information.
        :param short:  Whether to omit characters and artworks from the response. Requires extended=True to work.
        :param meta:  The meta to fetch. Requires extended=True to work.
        :return:
        """
        media_id = parse_media_id(media_id)
        query: dict[str, str] = {}
        if extended:
            if meta:
                query["meta"] = meta.value
            if short:
                query["short"] = "true"
            else:
                query["short"] = "false"
        elif meta:
            raise BadCallError("Meta can only be used with extended=True.")
        response = await client.request(
            "GET",
            f"{cls.ENDPOINT}/{media_id}" + ("/extended" if extended else ""),
            query=query if query else None,
        )
        response = cls.ResponseType(**response) if not extended else cls.ExtendedResponseType(**response)  # pyright: ignore[reportCallIssue]
        return cls(client, response.data)


@final
class Movie(_Media):
    """Class to interact with the TVDB API for movies."""

    ENDPOINT: ClassVar[str] = "movies"

    ResponseType = MoviesIdGetResponse
    ExtendedResponseType = MoviesIdExtendedGetResponse

    @override
    @classmethod
    async def supports_meta(cls, meta: FetchMeta) -> bool:
        """Check if the class supports a specific meta."""
        return meta is FetchMeta.TRANSLATIONS


@final
class Series(_Media):
    """Class to interact with the TVDB API for series."""

    ENDPOINT: ClassVar[str] = "series"

    ResponseType = SeriesIdGetResponse
    ExtendedResponseType = SeriesIdExtendedGetResponse

    @override
    @classmethod
    async def supports_meta(cls, meta: FetchMeta) -> bool:
        """Check if the class supports a specific meta."""
        return meta in {FetchMeta.TRANSLATIONS, FetchMeta.EPISODES}


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
        self, search_query: str, entity_type: Literal["series", "movie", None] = None, limit: int = 1
    ) -> list[Movie | Series]:
        """Search for a series or movie in the TVDB database."""
        query: dict[str, str] = {"query": search_query, "limit": str(limit)}
        if entity_type:
            query["type"] = entity_type
        data = await self.request("GET", "search", query=query)
        response = SearchGetResponse(**data)  # pyright: ignore[reportCallIssue]
        if not response.data:
            raise ValueError("This should not happen.")
        returnable: list[Movie | Series] = []
        for result in response.data:
            match result.type:
                case "movie":
                    returnable.append(Movie(self, result))
                case "series":
                    returnable.append(Series(self, result))
                case _:
                    pass
        return returnable

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
