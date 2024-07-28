from abc import ABC, abstractmethod
from datetime import UTC, datetime
from enum import Enum
from typing import ClassVar, Literal, Self, final, overload, override

import aiohttp
from aiocache import BaseCache
from yarl import URL

from src.settings import TVDB_API_KEY, TVDB_RATE_LIMIT_PERIOD, TVDB_RATE_LIMIT_REQUESTS
from src.tvdb.errors import BadCallError, InvalidApiKeyError, InvalidIdError
from src.tvdb.generated_models import (
    EpisodeBaseRecord,
    EpisodeExtendedRecord,
    EpisodesIdExtendedGetResponse,
    EpisodesIdGetResponse,
    MovieBaseRecord,
    MovieExtendedRecord,
    MoviesIdExtendedGetResponse,
    MoviesIdGetResponse,
    SearchGetResponse,
    SearchResult,
    SeasonBaseRecord,
    SeriesBaseRecord,
    SeriesExtendedRecord,
    SeriesIdEpisodesSeasonTypeGetResponse,
    SeriesIdExtendedGetResponse,
    SeriesIdGetResponse,
)
from src.utils.iterators import get_first
from src.utils.log import get_logger
from src.utils.ratelimit import rate_limit

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
        media_id = int(str(media_id).removeprefix("movie-").removeprefix("series-").removeprefix("episode-"))
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
        self.client = client
        self.set_attributes(data)

    def set_attributes(self, data: AnyRecord | SearchResult) -> None:
        """Setting attributes."""
        self.data = data
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
                self.name_eng = get_first(alias.name for alias in self.data.aliases if alias.language == "eng")
            if isinstance(self.data, (SeriesExtendedRecord, MovieExtendedRecord)) and self.data.translations:
                if self.data.translations.name_translations:
                    self.name_eng = get_first(
                        translation.name
                        for translation in self.data.translations.name_translations
                        if translation.language == "eng"
                    )
                if self.data.translations.overview_translations:
                    self.overview_eng = get_first(
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
    @overload
    async def fetch(
        cls,
        media_id: int | str,
        client: "TvdbClient",
        *,
        extended: Literal[False] = False,
        short: Literal[False] | None = None,
        meta: None = None,
    ) -> Self: ...

    @classmethod
    @overload
    async def fetch(
        cls,
        media_id: int | str,
        client: "TvdbClient",
        *,
        extended: Literal[True],
        short: bool | None = None,
        meta: FetchMeta | None = None,
    ) -> Self: ...

    @classmethod
    async def fetch(
        cls,
        media_id: int | str,
        client: "TvdbClient",
        *,
        extended: bool = False,
        short: bool | None = None,
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
        cache_key: str = f"{media_id}"
        if extended:
            cache_key += f"_{bool(short)}"
            if meta:
                cache_key += f"_{meta.value}"
        response = await client.cache.get(cache_key, namespace=f"tvdb_{cls.ENDPOINT}")
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
        elif short:
            raise BadCallError("Short can only be enabled with extended=True.")
        if not response:
            response = await client.request(
                "GET",
                f"{cls.ENDPOINT}/{media_id}" + ("/extended" if extended else ""),
                query=query if query else None,
            )
            await client.cache.set(key=cache_key, value=response, ttl=60 * 60, namespace=f"tvdb_{cls.ENDPOINT}")
            log.trace(f"Stored into cache: {cache_key}")
        else:
            log.trace(f"Loaded from cache: {cache_key}")
        response = cls.ResponseType(**response) if not extended else cls.ExtendedResponseType(**response)  # pyright: ignore[reportCallIssue]

        return cls(client, response.data)

    async def ensure_translations(self) -> None:
        """Ensure that response contains translations."""
        if not isinstance(self.data, SeriesExtendedRecord):
            series = await self.fetch(
                media_id=self.id, client=self.client, extended=True, short=True, meta=FetchMeta.TRANSLATIONS
            )
            self.set_attributes(series.data)


@final
class Movie(_Media):
    """Class to interact with the TVDB API for movies."""

    ENDPOINT: ClassVar[str] = "movies"
    data: SearchResult | MovieBaseRecord | MovieExtendedRecord

    ResponseType = MoviesIdGetResponse
    ExtendedResponseType = MoviesIdExtendedGetResponse

    @override
    def set_attributes(self, data: AnyRecord | SearchResult) -> None:
        super().set_attributes(data)
        self.url: str | None = f"https://www.thetvdb.com/movies/{self.slug}" if self.slug else None

    @override
    @classmethod
    async def supports_meta(cls, meta: FetchMeta) -> bool:
        """Check if the class supports a specific meta."""
        return meta is FetchMeta.TRANSLATIONS


@final
class Series(_Media):
    """Class to interact with the TVDB API for series."""

    ENDPOINT: ClassVar[str] = "series"
    data: SearchResult | SeriesBaseRecord | SeriesExtendedRecord

    ResponseType = SeriesIdGetResponse
    ExtendedResponseType = SeriesIdExtendedGetResponse

    def __init__(self, client: "TvdbClient", data: AnyRecord | SearchResult | None):
        super().__init__(client, data)

    @override
    def set_attributes(self, data: SearchResult | SeriesBaseRecord | SeriesExtendedRecord) -> None:
        super().set_attributes(data)
        self.episodes: list[Episode] | None = None
        self.seasons: list[SeasonBaseRecord] | None = None
        if isinstance(self.data, SeriesExtendedRecord):
            self.seasons = self.data.seasons
            if self.data.episodes:
                self.episodes = [Episode(episode, client=self.client) for episode in self.data.episodes]
        self.url: str | None = f"https://www.thetvdb.com/series/{self.slug}" if self.slug else None

    @override
    @classmethod
    async def supports_meta(cls, meta: FetchMeta) -> bool:
        """Check if the class supports a specific meta."""
        return meta in {FetchMeta.TRANSLATIONS, FetchMeta.EPISODES}

    async def fetch_episodes(self, season_type: str = "official") -> None:
        """Fetch episodes for the series based on the season type."""
        cache_key: str = f"{self.id}_{season_type}"
        endpoint = f"series/{self.id}/episodes/{season_type}"
        response = await self.client.cache.get(cache_key, namespace="tvdb_episodes")
        if not response:
            response = await self.client.request("GET", endpoint)
            await self.client.cache.set(cache_key, value=response, namespace="tvdb_episodes", ttl=60 * 60)
            log.trace(f"Stored into cache: {cache_key}")
        else:
            log.trace(f"Loaded from cache: {cache_key}")

        # Assuming 'episodes' field contains the list of episodes
        response = SeriesIdEpisodesSeasonTypeGetResponse(**response)  # pyright: ignore[reportCallIssue]

        if response.data and response.data.episodes:
            self.episodes = [Episode(episode, client=self.client) for episode in response.data.episodes]

    async def ensure_seasons_and_episodes(self) -> None:
        """Ensure that reponse contains seasons."""
        if not isinstance(self.data, SeriesExtendedRecord):
            series = await self.fetch(
                media_id=self.id, client=self.client, extended=True, short=True, meta=FetchMeta.EPISODES
            )
            self.set_attributes(series.data)


class Episode:
    """Represents an episode from Tvdb."""

    def __init__(self, data: EpisodeBaseRecord | EpisodeExtendedRecord, client: "TvdbClient") -> None:
        self.client = client
        self.set_attributes(data)

    def set_attributes(self, data: EpisodeBaseRecord | EpisodeExtendedRecord) -> None:
        """Set attributes."""
        self.data = data
        self.id: int | None = self.data.id
        self.image_url: str | None = self.data.image if self.data.image else None
        self.name: str | None = self.data.name
        self.overview: str | None = self.data.overview
        self.number: int | None = self.data.number
        self.season_number: int | None = self.data.season_number
        self.name_eng: str | None = None
        self.overview_eng: str | None = None
        self.series_id: int | None = self.data.series_id
        self.air_date: datetime | None = None
        if self.data.aired:
            self.air_date = datetime.strptime(self.data.aired, "%Y-%m-%d").replace(tzinfo=UTC)
        self.aired: bool = self.air_date is not None and self.air_date <= datetime.now(UTC)

        if isinstance(self.data, EpisodeExtendedRecord):
            if self.data.translations and self.data.translations.name_translations:
                self.name_eng = get_first(
                    translation.name
                    for translation in self.data.translations.name_translations
                    if translation.language == "eng"
                )

            if self.data.translations and self.data.translations.overview_translations:
                self.overview_eng = get_first(
                    translation.overview
                    for translation in self.data.translations.overview_translations
                    if translation.language == "eng"
                )

    @property
    def formatted_name(self) -> str:
        """Returns the name in format SxxEyy - Name."""
        return f"S{self.season_number:02}E{self.number:02} - {self.name}"

    @classmethod
    async def fetch(cls, media_id: str | int, *, client: "TvdbClient", extended: bool = True) -> "Episode":
        """Fetch episode."""
        endpoint = f"/episodes/{parse_media_id(media_id)}"
        query: dict[str, str] | None = None

        if extended:
            endpoint += "/extended"
            query = {"meta": "translations"}
        response = await client.request("GET", endpoint=endpoint, query=query)
        response = EpisodesIdGetResponse(**response) if not extended else EpisodesIdExtendedGetResponse(**response)  # pyright: ignore[reportCallIssue]

        if not response.data:
            raise ValueError("No data found for Episode")
        return cls(response.data, client=client)

    async def ensure_translations(self) -> None:
        """Ensure that response contains translations."""
        if not isinstance(self.data, EpisodeExtendedRecord):
            if not self.id:
                raise ValueError("Episode has no ID")
            episode = await self.fetch(self.id, client=self.client, extended=True)
            self.set_attributes(episode.data)

    async def fetch_series(
        self, *, extended: bool = False, short: bool | None = None, meta: FetchMeta | None = None
    ) -> Series:
        """Fetching series."""
        if not self.series_id:
            raise ValueError("Series Id cannot be None.")
        return await Series.fetch(  # pyright: ignore[reportCallIssue]
            client=self.client,
            media_id=self.series_id,
            extended=extended,  # pyright: ignore[reportArgumentType]
            short=short,
            meta=meta,
        )

    @property
    def bilingual_name(self) -> str | None:
        """Returns the name in both languages."""
        if self.name == self.name_eng:
            return self.name
        return f"{self.name} ({self.name_eng})"


class TvdbClient:
    """Class to interact with the TVDB API."""

    BASE_URL: ClassVar[URL] = URL("https://api4.thetvdb.com/v4/")

    def __init__(self, http_session: aiohttp.ClientSession, cache: BaseCache):
        self.http_session = http_session
        self.auth_token = None
        self.cache = cache

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

        # TODO: It would be better to instead use a queue to handle rate-limits
        # and block until the next request can be made.
        await rate_limit(
            self.cache,
            "tvdb",
            limit=TVDB_RATE_LIMIT_REQUESTS,
            period=TVDB_RATE_LIMIT_PERIOD,
            err_msg="Bot wide rate-limit for TheTVDB API was exceeded.",
        )

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
        cache_key: str = f"{search_query}_{entity_type}_{limit}"
        data = await self.cache.get(cache_key, namespace="tvdb_search")
        if not data:
            query: dict[str, str] = {"query": search_query, "limit": str(limit)}
            if entity_type:
                query["type"] = entity_type
            data = await self.request("GET", "search", query=query)
            await self.cache.set(key=cache_key, value=data, ttl=60 * 60, namespace="tvdb_search")
            log.trace(f"Stored into cache: {cache_key}")
        else:
            log.trace(f"Loaded from cache: {cache_key}")
        response = SearchGetResponse(**data)  # pyright: ignore[reportCallIssue]
        returnable: list[Movie | Series] = []
        if not response.data:
            return returnable
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
