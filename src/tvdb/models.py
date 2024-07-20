from pydantic import BaseModel


class _RemoteID(BaseModel):
    id: str
    type: int
    sourceName: str  # noqa: N815


class _Translation(BaseModel):
    ara: str | None = None
    ces: str | None = None
    deu: str | None = None


class SearchData(BaseModel):
    """Model for the data objects returned by the TVDB search endpoint."""

    aliases: list[str]
    companies: list[str] | None = None
    companyType: str | None = None  # noqa: N815
    country: str
    director: str | None = None
    first_air_time: str
    genres: list[str] | None = None
    id: str
    image_url: str
    name: str
    is_official: bool | None = None
    name_translated: str | None = None
    network: str
    objectID: str  # noqa: N815
    officialList: str | None = None  # noqa: N815
    overview: str
    overviews: _Translation
    overview_translated: list[str] | None = None
    poster: str | None = None
    posters: list[str] | None = None
    primary_language: str
    remote_ids: list[_RemoteID]
    status: str
    slug: str
    studios: list[str] | None = None
    title: str | None = None
    thumbnail: str
    translations: _Translation
    translationsWithLang: list[str] | None = None  # noqa: N815
    tvdb_id: str
    type: str
    year: str


class _Links(BaseModel):
    prev: str | None = None  # none if on the first page
    self: str
    next: str
    total_items: int
    page_size: int


class SearchResponse(BaseModel):
    """Model for the response from the TVDB search endpoint."""

    data: list[SearchData]
    status: str
    links: _Links
