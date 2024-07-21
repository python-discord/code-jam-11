import aiohttp


class TVDBError(Exception):
    """The base exception for all TVDB errors."""


class BadCallError(TVDBError):
    """Exception raised when the meta value is incompatible with the class."""


class InvalidIdError(TVDBError):
    """Exception raised when the ID provided is invalid."""


class InvalidApiKeyError(TVDBError):
    """Exception raised when the TVDB API key used was invalid."""

    def __init__(self, response: aiohttp.ClientResponse, response_txt: str):
        self.response = response
        self.response_txt = response_txt
        super().__init__("Invalid TVDB API key.")
