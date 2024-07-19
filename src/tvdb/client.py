from typing import ClassVar, Literal, overload

import aiohttp
from yarl import URL

from src.settings import TVDB_API_KEY
from src.utils.log import get_logger

log = get_logger(__name__)

type JSON_DATA = dict[str, JSON_DATA] | list[JSON_DATA] | str | int | float | bool | None


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
    async def request(self, method: Literal["GET"], endpoint: str, body: None = None) -> JSON_DATA: ...

    @overload
    async def request(self, method: Literal["POST"], endpoint: str, body: JSON_DATA) -> JSON_DATA: ...

    async def request(self, method: Literal["GET", "POST"], endpoint: str, body: JSON_DATA = None) -> JSON_DATA:
        """Make an authorized request to the TVDB API."""
        log.trace(f"Making TVDB {method} request to {endpoint}")

        if self.auth_token is None:
            log.trace("No auth token found, requesting initial login.")
            await self._login()
        headers = {"Authorization": f"Bearer {self.auth_token}"}

        url = self.BASE_URL / endpoint.removeprefix("/")
        async with self.http_session.request(method, url, headers=headers, json=body) as response:
            if response.status == 401:
                log.debug("TVDB API token expired, requesting new token.")
                self.auth_token = None
                return await self.request(method, endpoint, body)  # pyright: ignore[reportCallIssue,reportArgumentType]

            response.raise_for_status()
            return await response.json()

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
