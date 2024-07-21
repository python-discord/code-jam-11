# ruff: noqa: D101 # Allow missing docstrings

from __future__ import annotations

from pydantic import BaseModel, Field, RootModel


class Alias(BaseModel):
    language: str = Field(le=4)
    """
    A 3-4 character string indicating the language of the alias, as defined in Language.
    """
    name: str = Field(le=100)
    """
    A string containing the alias itself.
    """


class ArtworkBaseRecord(BaseModel):
    height: int | None = Field(default=None, json_schema_extra={"x-go-name": "Height"})
    id: int | None = None
    image: str | None = Field(default=None, json_schema_extra={"x-go-name": "Image"})
    includes_text: bool | None = Field(default=None, alias="includesText")
    language: str | None = None
    score: float | None = None
    thumbnail: str | None = Field(default=None, json_schema_extra={"x-go-name": "Thumbnail"})
    type: int | None = Field(default=None, json_schema_extra={"x-go-name": "Type"})
    """
    The artwork type corresponds to the ids from the /artwork/types endpoint.
    """
    width: int | None = Field(default=None, json_schema_extra={"x-go-name": "Width"})


class ArtworkStatus(BaseModel):
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    name: str | None = None


class ArtworkType(BaseModel):
    height: int | None = None
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    image_format: str | None = Field(
        default=None,
        alias="imageFormat",
        json_schema_extra={"x-go-name": "ImageFormat"},
    )
    name: str | None = Field(default=None, json_schema_extra={"x-go-name": "Name"})
    record_type: str | None = Field(default=None, alias="recordType", json_schema_extra={"x-go-name": "RecordType"})
    slug: str | None = Field(default=None, json_schema_extra={"x-go-name": "Slug"})
    thumb_height: int | None = Field(
        default=None,
        alias="thumbHeight",
        json_schema_extra={"x-go-name": "ThumbHeight"},
    )
    thumb_width: int | None = Field(default=None, alias="thumbWidth", json_schema_extra={"x-go-name": "ThumbWidth"})
    width: int | None = Field(default=None, json_schema_extra={"x-go-name": "Width"})


class AwardBaseRecord(BaseModel):
    id: int | None = None
    name: str | None = None


class AwardCategoryBaseRecord(BaseModel):
    allow_co_nominees: bool | None = Field(
        default=None,
        alias="allowCoNominees",
        json_schema_extra={"x-go-name": "AllowCoNominees"},
    )
    award: AwardBaseRecord | None = None
    for_movies: bool | None = Field(default=None, alias="forMovies", json_schema_extra={"x-go-name": "ForMovies"})
    for_series: bool | None = Field(default=None, alias="forSeries", json_schema_extra={"x-go-name": "ForSeries"})
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    name: str | None = None


class AwardExtendedRecord(BaseModel):
    categories: list[AwardCategoryBaseRecord] | None = Field(
        default=None, json_schema_extra={"x-go-name": "Categories"}
    )
    id: int | None = None
    name: str | None = None
    score: int | None = Field(default=None, json_schema_extra={"x-go-name": "Score"})


class Biography(BaseModel):
    biography: str | None = Field(default=None, json_schema_extra={"x-go-name": "Biography"})
    language: str | None = Field(default=None, json_schema_extra={"x-go-name": "Language"})


class CompanyRelationShip(BaseModel):
    id: int | None = None
    type_name: str | None = Field(default=None, alias="typeName")


class CompanyType(BaseModel):
    company_type_id: int | None = Field(default=None, alias="companyTypeId")
    company_type_name: str | None = Field(default=None, alias="companyTypeName")


class ContentRating(BaseModel):
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    name: str | None = Field(default=None, json_schema_extra={"x-go-name": "Name"})
    description: str | None = None
    country: str | None = None
    content_type: str | None = Field(default=None, alias="contentType")
    order: int | None = None
    full_name: str | None = Field(default=None, alias="fullName")


class Country(BaseModel):
    id: str | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    name: str | None = Field(default=None, json_schema_extra={"x-go-name": "Name"})
    short_code: str | None = Field(default=None, alias="shortCode", json_schema_extra={"x-go-name": "ShortCode"})


class Entity(BaseModel):
    movie_id: int | None = Field(default=None, alias="movieId")
    order: int | None = Field(default=None, json_schema_extra={"x-go-name": "Order"})
    series_id: int | None = Field(default=None, alias="seriesId")


class EntityType(BaseModel):
    id: int | None = None
    name: str | None = Field(default=None, json_schema_extra={"x-go-name": "Order"})
    has_specials: bool | None = Field(default=None, alias="hasSpecials")


class EntityUpdate(BaseModel):
    entity_type: str | None = Field(default=None, alias="entityType", json_schema_extra={"x-go-name": "EnitityType"})
    method_int: int | None = Field(default=None, alias="methodInt")
    method: str | None = Field(default=None, json_schema_extra={"x-go-name": "Method"})
    extra_info: str | None = Field(default=None, alias="extraInfo")
    user_id: int | None = Field(default=None, alias="userId")
    record_type: str | None = Field(default=None, alias="recordType")
    record_id: int | None = Field(default=None, alias="recordId", json_schema_extra={"x-go-name": "RecordID"})
    time_stamp: int | None = Field(default=None, alias="timeStamp", json_schema_extra={"x-go-name": "TimeStamp"})
    series_id: int | None = Field(default=None, alias="seriesId", json_schema_extra={"x-go-name": "RecordID"})
    """
    Only present for episodes records
    """
    merge_to_id: int | None = Field(default=None, alias="mergeToId")
    merge_to_entity_type: str | None = Field(default=None, alias="mergeToEntityType")


class Favorites(BaseModel):
    series: list[int] | None = Field(default=None, json_schema_extra={"x-go-name": "series"})
    movies: list[int] | None = Field(default=None, json_schema_extra={"x-go-name": "movies"})
    episodes: list[int] | None = Field(default=None, json_schema_extra={"x-go-name": "episodes"})
    artwork: list[int] | None = Field(default=None, json_schema_extra={"x-go-name": "artwork"})
    people: list[int] | None = Field(default=None, json_schema_extra={"x-go-name": "people"})
    lists: list[int] | None = Field(default=None, json_schema_extra={"x-go-name": "list"})


class FavoriteRecord(BaseModel):
    series: int | None = Field(default=None, json_schema_extra={"x-go-name": "series"})
    movie: int | None = Field(default=None, json_schema_extra={"x-go-name": "movies"})
    episode: int | None = Field(default=None, json_schema_extra={"x-go-name": "episodes"})
    artwork: int | None = Field(default=None, json_schema_extra={"x-go-name": "artwork"})
    people: int | None = Field(default=None, json_schema_extra={"x-go-name": "people"})
    list: int | None = Field(default=None, json_schema_extra={"x-go-name": "list"})


class Gender(BaseModel):
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    name: str | None = Field(default=None, json_schema_extra={"x-go-name": "Name"})


class GenreBaseRecord(BaseModel):
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    name: str | None = Field(default=None, json_schema_extra={"x-go-name": "Name"})
    slug: str | None = Field(default=None, json_schema_extra={"x-go-name": "Slug"})


class Language(BaseModel):
    id: str | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    name: str | None = Field(default=None, json_schema_extra={"x-go-name": "Name"})
    native_name: str | None = Field(default=None, alias="nativeName", json_schema_extra={"x-go-name": "NativeName"})
    short_code: str | None = Field(default=None, alias="shortCode")


class ListExtendedRecord(BaseModel):
    aliases: list[Alias] | None = Field(default=None, json_schema_extra={"x-go-name": "Aliases"})
    entities: list[Entity] | None = Field(default=None, json_schema_extra={"x-go-name": "Entities"})
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    image: str | None = None
    image_is_fallback: bool | None = Field(default=None, alias="imageIsFallback")
    is_official: bool | None = Field(default=None, alias="isOfficial", json_schema_extra={"x-go-name": "IsOfficial"})
    name: str | None = None
    name_translations: list[str] | None = Field(
        default=None,
        alias="nameTranslations",
        json_schema_extra={"x-go-name": "NameTranslations"},
    )
    overview: str | None = None
    overview_translations: list[str] | None = Field(
        default=None,
        alias="overviewTranslations",
        json_schema_extra={"x-go-name": "OverviewTranslations"},
    )
    score: int | None = Field(default=None, json_schema_extra={"x-go-name": "Score"})
    url: str | None = None


class PeopleBaseRecord(BaseModel):
    aliases: list[Alias] | None = Field(default=None, json_schema_extra={"x-go-name": "Aliases"})
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    image: str | None = None
    last_updated: str | None = Field(default=None, alias="lastUpdated")
    name: str | None = None
    name_translations: list[str] | None = Field(
        default=None,
        alias="nameTranslations",
        json_schema_extra={"x-go-name": "NameTranslations"},
    )
    overview_translations: list[str] | None = Field(
        default=None,
        alias="overviewTranslations",
        json_schema_extra={"x-go-name": "OverviewTranslations"},
    )
    score: int | None = Field(default=None, json_schema_extra={"x-go-name": "Score"})


class PeopleType(Gender):
    pass


class Race(BaseModel):
    pass


class RecordInfo(BaseModel):
    image: str | None = Field(default=None, json_schema_extra={"x-go-name": "Image"})
    name: str | None = Field(default=None, json_schema_extra={"x-go-name": "Name"})
    year: str | None = None


class Release(BaseModel):
    country: str | None = None
    date: str | None = None
    detail: str | None = None


class RemoteID(BaseModel):
    id: str | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    type: int | None = Field(default=None, json_schema_extra={"x-go-name": "Type"})
    source_name: str | None = Field(default=None, alias="sourceName", json_schema_extra={"x-go-name": "SourceName"})


class SeasonType(BaseModel):
    alternate_name: str | None = Field(default=None, alias="alternateName", json_schema_extra={"x-go-name": "Name"})
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    name: str | None = Field(default=None, json_schema_extra={"x-go-name": "Name"})
    type: str | None = Field(default=None, json_schema_extra={"x-go-name": "Type"})


class SeriesAirsDays(BaseModel):
    friday: bool | None = Field(default=None, json_schema_extra={"x-go-name": "Friday"})
    monday: bool | None = Field(default=None, json_schema_extra={"x-go-name": "Monday"})
    saturday: bool | None = Field(default=None, json_schema_extra={"x-go-name": "Saturday"})
    sunday: bool | None = Field(default=None, json_schema_extra={"x-go-name": "Sunday"})
    thursday: bool | None = Field(default=None, json_schema_extra={"x-go-name": "Thursday"})
    tuesday: bool | None = Field(default=None, json_schema_extra={"x-go-name": "Tuesday"})
    wednesday: bool | None = Field(default=None, json_schema_extra={"x-go-name": "Wednesday"})


class SourceType(BaseModel):
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    name: str | None = Field(default=None, json_schema_extra={"x-go-name": "Name"})
    postfix: str | None = None
    prefix: str | None = None
    slug: str | None = Field(default=None, json_schema_extra={"x-go-name": "Slug"})
    sort: int | None = Field(default=None, json_schema_extra={"x-go-name": "Sort"})


class Status(BaseModel):
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    keep_updated: bool | None = Field(
        default=None,
        alias="keepUpdated",
        json_schema_extra={"x-go-name": "KeepUpdated"},
    )
    name: str | None = Field(default=None, json_schema_extra={"x-go-name": "Name"})
    record_type: str | None = Field(default=None, alias="recordType", json_schema_extra={"x-go-name": "RecordType"})


class StudioBaseRecord(BaseModel):
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    name: str | None = Field(default=None, json_schema_extra={"x-go-name": "Name"})
    parent_studio: int | None = Field(default=None, alias="parentStudio")


class TagOption(BaseModel):
    help_text: str | None = Field(default=None, alias="helpText")
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    name: str | None = Field(default=None, json_schema_extra={"x-go-name": "Name"})
    tag: int | None = Field(default=None, json_schema_extra={"x-go-name": "Tag"})
    tag_name: str | None = Field(default=None, alias="tagName", json_schema_extra={"x-go-name": "TagName"})


class Trailer(BaseModel):
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    language: str | None = None
    name: str | None = None
    url: str | None = None
    runtime: int | None = None


class Translation(BaseModel):
    aliases: list[str] | None = None
    is_alias: bool | None = Field(default=None, alias="isAlias")
    is_primary: bool | None = Field(default=None, alias="isPrimary")
    language: str | None = Field(default=None, json_schema_extra={"x-go-name": "Language"})
    name: str | None = None
    overview: str | None = None
    tagline: str | None = None
    """
    Only populated for movie translations.  We disallow taglines without a title.
    """


class TranslationSimple(RootModel[dict[str, str] | None]):
    root: dict[str, str] | None = None


class TranslationExtended(BaseModel):
    name_translations: list[Translation] | None = Field(default=None, alias="nameTranslations")
    overview_translations: list[Translation] | None = Field(default=None, alias="overviewTranslations")
    alias: list[str] | None = None


class TagOptionEntity(BaseModel):
    name: str | None = None
    tag_name: str | None = Field(default=None, alias="tagName")
    tag_id: int | None = Field(default=None, alias="tagId")


class UserInfo(BaseModel):
    id: int | None = None
    language: str | None = None
    name: str | None = None
    type: str | None = None


class Inspiration(BaseModel):
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    type: str | None = None
    type_name: str | None = None
    url: str | None = None


class InspirationType(BaseModel):
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    name: str | None = None
    description: str | None = None
    reference_name: str | None = None
    url: str | None = None


class ProductionCountry(BaseModel):
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    country: str | None = None
    name: str | None = None


class Links(BaseModel):
    prev: str | None = None
    self: str | None = None
    next: str | None = None
    total_items: int | None = None
    page_size: int | None = None


class ArtworkExtendedRecord(BaseModel):
    episode_id: int | None = Field(default=None, alias="episodeId")
    height: int | None = Field(default=None, json_schema_extra={"x-go-name": "Height"})
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    image: str | None = Field(default=None, json_schema_extra={"x-go-name": "Image"})
    includes_text: bool | None = Field(default=None, alias="includesText")
    language: str | None = None
    movie_id: int | None = Field(default=None, alias="movieId")
    network_id: int | None = Field(default=None, alias="networkId")
    people_id: int | None = Field(default=None, alias="peopleId")
    score: float | None = None
    season_id: int | None = Field(default=None, alias="seasonId")
    series_id: int | None = Field(default=None, alias="seriesId")
    series_people_id: int | None = Field(default=None, alias="seriesPeopleId")
    status: ArtworkStatus | None = None
    tag_options: list[TagOption] | None = Field(
        default=None, alias="tagOptions", json_schema_extra={"x-go-name": "TagOptions"}
    )
    thumbnail: str | None = Field(default=None, json_schema_extra={"x-go-name": "Thumbnail"})
    thumbnail_height: int | None = Field(
        default=None,
        alias="thumbnailHeight",
        json_schema_extra={"x-go-name": "ThumbnailHeight"},
    )
    thumbnail_width: int | None = Field(
        default=None,
        alias="thumbnailWidth",
        json_schema_extra={"x-go-name": "ThumbnailWidth"},
    )
    type: int | None = Field(default=None, json_schema_extra={"x-go-name": "Type"})
    """
    The artwork type corresponds to the ids from the /artwork/types endpoint.
    """
    updated_at: int | None = Field(default=None, alias="updatedAt", json_schema_extra={"x-go-name": "UpdatedAt"})
    width: int | None = Field(default=None, json_schema_extra={"x-go-name": "Width"})


class Character(BaseModel):
    aliases: list[Alias] | None = Field(default=None, json_schema_extra={"x-go-name": "Aliases"})
    episode: RecordInfo | None = None
    episode_id: int | None = Field(default=None, alias="episodeId")
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    image: str | None = None
    is_featured: bool | None = Field(default=None, alias="isFeatured", json_schema_extra={"x-go-name": "IsFeatured"})
    movie_id: int | None = Field(default=None, alias="movieId")
    movie: RecordInfo | None = None
    name: str | None = None
    name_translations: list[str] | None = Field(
        default=None,
        alias="nameTranslations",
        json_schema_extra={"x-go-name": "NameTranslations"},
    )
    overview_translations: list[str] | None = Field(
        default=None,
        alias="overviewTranslations",
        json_schema_extra={"x-go-name": "OverviewTranslations"},
    )
    people_id: int | None = Field(default=None, alias="peopleId")
    person_img_url: str | None = Field(default=None, alias="personImgURL")
    people_type: str | None = Field(default=None, alias="peopleType")
    series_id: int | None = Field(default=None, alias="seriesId")
    series: RecordInfo | None = None
    sort: int | None = Field(default=None, json_schema_extra={"x-go-name": "Sort"})
    tag_options: list[TagOption] | None = Field(
        default=None, alias="tagOptions", json_schema_extra={"x-go-name": "TagOptions"}
    )
    type: int | None = Field(default=None, json_schema_extra={"x-go-name": "Type"})
    url: str | None = Field(default=None, json_schema_extra={"x-go-name": "URL"})
    person_name: str | None = Field(default=None, alias="personName")


class ParentCompany(BaseModel):
    id: int | None = None
    name: str | None = None
    relation: CompanyRelationShip | None = None


class ListBaseRecord(BaseModel):
    aliases: list[Alias] | None = Field(default=None, json_schema_extra={"x-go-name": "Aliases"})
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    image: str | None = None
    image_is_fallback: bool | None = Field(default=None, alias="imageIsFallback")
    is_official: bool | None = Field(default=None, alias="isOfficial", json_schema_extra={"x-go-name": "IsOfficial"})
    name: str | None = None
    name_translations: list[str] | None = Field(
        default=None,
        alias="nameTranslations",
        json_schema_extra={"x-go-name": "NameTranslations"},
    )
    overview: str | None = None
    overview_translations: list[str] | None = Field(
        default=None,
        alias="overviewTranslations",
        json_schema_extra={"x-go-name": "OverviewTranslations"},
    )
    remote_ids: list[RemoteID] | None = Field(
        default=None, alias="remoteIds", json_schema_extra={"x-go-name": "RemoteIDs"}
    )
    tags: list[TagOption] | None = Field(default=None, json_schema_extra={"x-go-name": "TagOptions"})
    score: int | None = None
    url: str | None = None


class MovieBaseRecord(BaseModel):
    aliases: list[Alias] | None = Field(default=None, json_schema_extra={"x-go-name": "Aliases"})
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    image: str | None = Field(default=None, json_schema_extra={"x-go-name": "Image"})
    last_updated: str | None = Field(default=None, alias="lastUpdated")
    name: str | None = Field(default=None, json_schema_extra={"x-go-name": "Name"})
    name_translations: list[str] | None = Field(
        default=None,
        alias="nameTranslations",
        json_schema_extra={"x-go-name": "NameTranslations"},
    )
    overview_translations: list[str] | None = Field(
        default=None,
        alias="overviewTranslations",
        json_schema_extra={"x-go-name": "OverviewTranslations"},
    )
    score: float | None = Field(default=None, json_schema_extra={"x-go-name": "Score"})
    slug: str | None = Field(default=None, json_schema_extra={"x-go-name": "Slug"})
    status: Status | None = None
    runtime: int | None = None
    year: str | None = None


class PeopleExtendedRecord(BaseModel):
    aliases: list[Alias] | None = Field(default=None, json_schema_extra={"x-go-name": "Aliases"})
    awards: list[AwardBaseRecord] | None = Field(default=None, json_schema_extra={"x-go-name": "Awards"})
    biographies: list[Biography] | None = Field(default=None, json_schema_extra={"x-go-name": "Biographies"})
    birth: str | None = None
    birth_place: str | None = Field(default=None, alias="birthPlace")
    characters: list[Character] | None = Field(default=None, json_schema_extra={"x-go-name": "Characters"})
    death: str | None = None
    gender: int | None = None
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    image: str | None = None
    last_updated: str | None = Field(default=None, alias="lastUpdated")
    name: str | None = None
    name_translations: list[str] | None = Field(
        default=None,
        alias="nameTranslations",
        json_schema_extra={"x-go-name": "NameTranslations"},
    )
    overview_translations: list[str] | None = Field(
        default=None,
        alias="overviewTranslations",
        json_schema_extra={"x-go-name": "OverviewTranslations"},
    )
    races: list[Race] | None = Field(default=None, json_schema_extra={"x-go-name": "Races"})
    remote_ids: list[RemoteID] | None = Field(
        default=None, alias="remoteIds", json_schema_extra={"x-go-name": "RemoteIDs"}
    )
    score: int | None = Field(default=None, json_schema_extra={"x-go-name": "Score"})
    slug: str | None = None
    tag_options: list[TagOption] | None = Field(
        default=None, alias="tagOptions", json_schema_extra={"x-go-name": "TagOptions"}
    )
    translations: TranslationExtended | None = None


class SearchResult(BaseModel):
    aliases: list[str] | None = None
    companies: list[str] | None = None
    company_type: str | None = Field(default=None, alias="companyType")
    country: str | None = None
    director: str | None = None
    first_air_time: str | None = None
    genres: list[str] | None = None
    id: str
    image_url: str | None = None
    name: str | None = None
    is_official: bool | None = None
    name_translated: str | None = None
    network: str | None = None
    object_id: str | None = Field(default=None, alias="objectID")
    official_list: str | None = Field(default=None, alias="officialList")
    overview: str | None = None
    overviews: TranslationSimple | None = None
    overview_translated: list[str] | None = None
    poster: str | None = None
    posters: list[str] | None = None
    primary_language: str | None = None
    remote_ids: list[RemoteID] | None = Field(default=None, json_schema_extra={"x-go-name": "RemoteIDs"})
    status: str | None = Field(default=None, json_schema_extra={"x-go-name": "Status"})
    slug: str | None = None
    studios: list[str] | None = None
    title: str | None = None
    thumbnail: str | None = None
    translations: TranslationSimple | None = None
    translations_with_lang: list[str] | None = Field(default=None, alias="translationsWithLang")
    tvdb_id: str | None = None
    type: str | None = None
    year: str | None = None


class Tag(BaseModel):
    allows_multiple: bool | None = Field(
        default=None,
        alias="allowsMultiple",
        json_schema_extra={"x-go-name": "AllowsMultiple"},
    )
    help_text: str | None = Field(default=None, alias="helpText")
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    name: str | None = Field(default=None, json_schema_extra={"x-go-name": "Name"})
    options: list[TagOption] | None = Field(default=None, json_schema_extra={"x-go-name": "TagOptions"})


class Company(BaseModel):
    active_date: str | None = Field(default=None, alias="activeDate")
    aliases: list[Alias] | None = Field(default=None, json_schema_extra={"x-go-name": "Aliases"})
    country: str | None = None
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    inactive_date: str | None = Field(default=None, alias="inactiveDate")
    name: str | None = None
    name_translations: list[str] | None = Field(
        default=None,
        alias="nameTranslations",
        json_schema_extra={"x-go-name": "NameTranslations"},
    )
    overview_translations: list[str] | None = Field(
        default=None,
        alias="overviewTranslations",
        json_schema_extra={"x-go-name": "OverviewTranslations"},
    )
    primary_company_type: int | None = Field(
        default=None,
        alias="primaryCompanyType",
        json_schema_extra={"x-go-name": "PrimaryCompanyType"},
    )
    slug: str | None = Field(default=None, json_schema_extra={"x-go-name": "Slug"})
    parent_company: ParentCompany | None = Field(default=None, alias="parentCompany")
    tag_options: list[TagOption] | None = Field(
        default=None, alias="tagOptions", json_schema_extra={"x-go-name": "TagOptions"}
    )


class Companies(BaseModel):
    studio: list[Company] | None = None
    network: list[Company] | None = None
    production: list[Company] | None = None
    distributor: list[Company] | None = None
    special_effects: list[Company] | None = None


class MovieExtendedRecord(BaseModel):
    aliases: list[Alias] | None = Field(default=None, json_schema_extra={"x-go-name": "Aliases"})
    artworks: list[ArtworkBaseRecord] | None = Field(default=None, json_schema_extra={"x-go-name": "Artworks"})
    audio_languages: list[str] | None = Field(
        default=None,
        alias="audioLanguages",
        json_schema_extra={"x-go-name": "AudioLanguages"},
    )
    awards: list[AwardBaseRecord] | None = Field(default=None, json_schema_extra={"x-go-name": "Awards"})
    box_office: str | None = Field(default=None, alias="boxOffice")
    box_office_us: str | None = Field(default=None, alias="boxOfficeUS")
    budget: str | None = None
    characters: list[Character] | None = Field(default=None, json_schema_extra={"x-go-name": "Characters"})
    companies: Companies | None = None
    content_ratings: list[ContentRating] | None = Field(default=None, alias="contentRatings")
    first_release: Release | None = None
    genres: list[GenreBaseRecord] | None = Field(default=None, json_schema_extra={"x-go-name": "Genres"})
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    image: str | None = Field(default=None, json_schema_extra={"x-go-name": "Image"})
    inspirations: list[Inspiration] | None = Field(default=None, json_schema_extra={"x-go-name": "Inspirations"})
    last_updated: str | None = Field(default=None, alias="lastUpdated")
    lists: list[ListBaseRecord] | None = None
    name: str | None = Field(default=None, json_schema_extra={"x-go-name": "Name"})
    name_translations: list[str] | None = Field(
        default=None,
        alias="nameTranslations",
        json_schema_extra={"x-go-name": "NameTranslations"},
    )
    original_country: str | None = Field(default=None, alias="originalCountry")
    original_language: str | None = Field(default=None, alias="originalLanguage")
    overview_translations: list[str] | None = Field(
        default=None,
        alias="overviewTranslations",
        json_schema_extra={"x-go-name": "OverviewTranslations"},
    )
    production_countries: list[ProductionCountry] | None = Field(
        default=None, json_schema_extra={"x-go-name": "ProductionCountries"}
    )
    releases: list[Release] | None = Field(default=None, json_schema_extra={"x-go-name": "Releases"})
    remote_ids: list[RemoteID] | None = Field(
        default=None, alias="remoteIds", json_schema_extra={"x-go-name": "RemoteIDs"}
    )
    runtime: int | None = None
    score: float | None = Field(default=None, json_schema_extra={"x-go-name": "Score"})
    slug: str | None = Field(default=None, json_schema_extra={"x-go-name": "Slug"})
    spoken_languages: list[str] | None = Field(default=None, json_schema_extra={"x-go-name": "SpokenLanguages"})
    status: Status | None = None
    studios: list[StudioBaseRecord] | None = Field(default=None, json_schema_extra={"x-go-name": "Studios"})
    subtitle_languages: list[str] | None = Field(
        default=None,
        alias="subtitleLanguages",
        json_schema_extra={"x-go-name": "SubtitleLanguages"},
    )
    tag_options: list[TagOption] | None = Field(
        default=None, alias="tagOptions", json_schema_extra={"x-go-name": "TagOptions"}
    )
    trailers: list[Trailer] | None = Field(default=None, json_schema_extra={"x-go-name": "Trailers"})
    translations: TranslationExtended | None = None
    year: str | None = None


class SeasonBaseRecord(BaseModel):
    id: int | None = None
    image: str | None = None
    image_type: int | None = Field(default=None, alias="imageType")
    last_updated: str | None = Field(default=None, alias="lastUpdated")
    name: str | None = None
    name_translations: list[str] | None = Field(
        default=None,
        alias="nameTranslations",
        json_schema_extra={"x-go-name": "NameTranslations"},
    )
    number: int | None = Field(default=None, json_schema_extra={"x-go-name": "Number"})
    overview_translations: list[str] | None = Field(
        default=None,
        alias="overviewTranslations",
        json_schema_extra={"x-go-name": "OverviewTranslations"},
    )
    companies: Companies | None = None
    series_id: int | None = Field(default=None, alias="seriesId", json_schema_extra={"x-go-name": "SeriesID"})
    type: SeasonType | None = None
    year: str | None = None


class EpisodeBaseRecord(BaseModel):
    absolute_number: int | None = Field(default=None, alias="absoluteNumber")
    aired: str | None = None
    airs_after_season: int | None = Field(default=None, alias="airsAfterSeason")
    airs_before_episode: int | None = Field(default=None, alias="airsBeforeEpisode")
    airs_before_season: int | None = Field(default=None, alias="airsBeforeSeason")
    finale_type: str | None = Field(default=None, alias="finaleType")
    """
    season, midseason, or series
    """
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    image: str | None = None
    image_type: int | None = Field(default=None, alias="imageType")
    is_movie: int | None = Field(default=None, alias="isMovie", json_schema_extra={"x-go-name": "IsMovie"})
    last_updated: str | None = Field(default=None, alias="lastUpdated")
    linked_movie: int | None = Field(default=None, alias="linkedMovie")
    name: str | None = None
    name_translations: list[str] | None = Field(
        default=None,
        alias="nameTranslations",
        json_schema_extra={"x-go-name": "NameTranslations"},
    )
    number: int | None = None
    overview: str | None = None
    overview_translations: list[str] | None = Field(
        default=None,
        alias="overviewTranslations",
        json_schema_extra={"x-go-name": "OverviewTranslations"},
    )
    runtime: int | None = None
    season_number: int | None = Field(default=None, alias="seasonNumber")
    seasons: list[SeasonBaseRecord] | None = Field(default=None, json_schema_extra={"x-go-name": "Seasons"})
    series_id: int | None = Field(default=None, alias="seriesId", json_schema_extra={"x-go-name": "SeriesID"})
    season_name: str | None = Field(default=None, alias="seasonName")
    year: str | None = None


class SeasonExtendedRecord(BaseModel):
    artwork: list[ArtworkBaseRecord] | None = Field(default=None, json_schema_extra={"x-go-name": "Artwork"})
    companies: Companies | None = None
    episodes: list[EpisodeBaseRecord] | None = Field(default=None, json_schema_extra={"x-go-name": "Episodes"})
    id: int | None = None
    image: str | None = None
    image_type: int | None = Field(default=None, alias="imageType")
    last_updated: str | None = Field(default=None, alias="lastUpdated")
    name: str | None = None
    name_translations: list[str] | None = Field(
        default=None,
        alias="nameTranslations",
        json_schema_extra={"x-go-name": "NameTranslations"},
    )
    number: int | None = Field(default=None, json_schema_extra={"x-go-name": "Number"})
    overview_translations: list[str] | None = Field(
        default=None,
        alias="overviewTranslations",
        json_schema_extra={"x-go-name": "OverviewTranslations"},
    )
    series_id: int | None = Field(default=None, alias="seriesId", json_schema_extra={"x-go-name": "SeriesID"})
    trailers: list[Trailer] | None = Field(default=None, json_schema_extra={"x-go-name": "Trailers"})
    type: SeasonType | None = None
    tag_options: list[TagOption] | None = Field(
        default=None, alias="tagOptions", json_schema_extra={"x-go-name": "TagOptions"}
    )
    translations: list[Translation] | None = None
    year: str | None = None


class SeriesBaseRecord(BaseModel):
    aliases: list[Alias] | None = Field(default=None, json_schema_extra={"x-go-name": "Aliases"})
    average_runtime: int | None = Field(default=None, alias="averageRuntime")
    country: str | None = None
    default_season_type: int | None = Field(
        default=None,
        alias="defaultSeasonType",
        json_schema_extra={"x-go-name": "DefaultSeasonType"},
    )
    episodes: list[EpisodeBaseRecord] | None = Field(default=None, json_schema_extra={"x-go-name": "Episodes"})
    first_aired: str | None = Field(default=None, alias="firstAired")
    id: int | None = None
    image: str | None = None
    is_order_randomized: bool | None = Field(
        default=None,
        alias="isOrderRandomized",
        json_schema_extra={"x-go-name": "IsOrderRandomized"},
    )
    last_aired: str | None = Field(default=None, alias="lastAired")
    last_updated: str | None = Field(default=None, alias="lastUpdated")
    name: str | None = None
    name_translations: list[str] | None = Field(
        default=None,
        alias="nameTranslations",
        json_schema_extra={"x-go-name": "NameTranslations"},
    )
    next_aired: str | None = Field(default=None, alias="nextAired", json_schema_extra={"x-go-name": "NextAired"})
    original_country: str | None = Field(default=None, alias="originalCountry")
    original_language: str | None = Field(default=None, alias="originalLanguage")
    overview_translations: list[str] | None = Field(
        default=None,
        alias="overviewTranslations",
        json_schema_extra={"x-go-name": "OverviewTranslations"},
    )
    score: float | None = Field(default=None, json_schema_extra={"x-go-name": "Score"})
    slug: str | None = None
    status: Status | None = None
    year: str | None = None


class SeriesExtendedRecord(BaseModel):
    abbreviation: str | None = None
    airs_days: SeriesAirsDays | None = Field(default=None, alias="airsDays")
    airs_time: str | None = Field(default=None, alias="airsTime")
    aliases: list[Alias] | None = Field(default=None, json_schema_extra={"x-go-name": "Aliases"})
    artworks: list[ArtworkExtendedRecord] | None = Field(default=None, json_schema_extra={"x-go-name": "Artworks"})
    average_runtime: int | None = Field(default=None, alias="averageRuntime")
    characters: list[Character] | None = Field(default=None, json_schema_extra={"x-go-name": "Characters"})
    content_ratings: list[ContentRating] | None = Field(default=None, alias="contentRatings")
    country: str | None = None
    default_season_type: int | None = Field(
        default=None,
        alias="defaultSeasonType",
        json_schema_extra={"x-go-name": "DefaultSeasonType"},
    )
    episodes: list[EpisodeBaseRecord] | None = Field(default=None, json_schema_extra={"x-go-name": "Episodes"})
    first_aired: str | None = Field(default=None, alias="firstAired")
    lists: list[ListBaseRecord] | None = None
    genres: list[GenreBaseRecord] | None = Field(default=None, json_schema_extra={"x-go-name": "Genres"})
    id: int | None = None
    image: str | None = None
    is_order_randomized: bool | None = Field(
        default=None,
        alias="isOrderRandomized",
        json_schema_extra={"x-go-name": "IsOrderRandomized"},
    )
    last_aired: str | None = Field(default=None, alias="lastAired")
    last_updated: str | None = Field(default=None, alias="lastUpdated")
    name: str | None = None
    name_translations: list[str] | None = Field(
        default=None,
        alias="nameTranslations",
        json_schema_extra={"x-go-name": "NameTranslations"},
    )
    companies: list[Company] | None = None
    next_aired: str | None = Field(default=None, alias="nextAired", json_schema_extra={"x-go-name": "NextAired"})
    original_country: str | None = Field(default=None, alias="originalCountry")
    original_language: str | None = Field(default=None, alias="originalLanguage")
    original_network: Company | None = Field(default=None, alias="originalNetwork")
    overview: str | None = None
    latest_network: Company | None = Field(default=None, alias="latestNetwork")
    overview_translations: list[str] | None = Field(
        default=None,
        alias="overviewTranslations",
        json_schema_extra={"x-go-name": "OverviewTranslations"},
    )
    remote_ids: list[RemoteID] | None = Field(
        default=None, alias="remoteIds", json_schema_extra={"x-go-name": "RemoteIDs"}
    )
    score: float | None = Field(default=None, json_schema_extra={"x-go-name": "Score"})
    seasons: list[SeasonBaseRecord] | None = Field(default=None, json_schema_extra={"x-go-name": "Seasons"})
    season_types: list[SeasonType] | None = Field(
        default=None, alias="seasonTypes", json_schema_extra={"x-go-name": "Seasons"}
    )
    slug: str | None = None
    status: Status | None = None
    tags: list[TagOption] | None = Field(default=None, json_schema_extra={"x-go-name": "TagOptions"})
    trailers: list[Trailer] | None = Field(default=None, json_schema_extra={"x-go-name": "Trailers"})
    translations: TranslationExtended | None = None
    year: str | None = None


class AwardNomineeBaseRecord(BaseModel):
    character: Character | None = None
    details: str | None = None
    episode: EpisodeBaseRecord | None = None
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    is_winner: bool | None = Field(default=None, alias="isWinner", json_schema_extra={"x-go-name": "IsWinner"})
    movie: MovieBaseRecord | None = None
    series: SeriesBaseRecord | None = None
    year: str | None = None
    category: str | None = None
    name: str | None = None


class EpisodeExtendedRecord(BaseModel):
    aired: str | None = None
    airs_after_season: int | None = Field(default=None, alias="airsAfterSeason")
    airs_before_episode: int | None = Field(default=None, alias="airsBeforeEpisode")
    airs_before_season: int | None = Field(default=None, alias="airsBeforeSeason")
    awards: list[AwardBaseRecord] | None = Field(default=None, json_schema_extra={"x-go-name": "Awards"})
    characters: list[Character] | None = Field(default=None, json_schema_extra={"x-go-name": "Characters"})
    companies: list[Company] | None = None
    content_ratings: list[ContentRating] | None = Field(
        default=None,
        alias="contentRatings",
        json_schema_extra={"x-go-name": "ContentRatings"},
    )
    finale_type: str | None = Field(default=None, alias="finaleType")
    """
    season, midseason, or series
    """
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    image: str | None = None
    image_type: int | None = Field(default=None, alias="imageType")
    is_movie: int | None = Field(default=None, alias="isMovie", json_schema_extra={"x-go-name": "IsMovie"})
    last_updated: str | None = Field(default=None, alias="lastUpdated")
    linked_movie: int | None = Field(default=None, alias="linkedMovie")
    name: str | None = None
    name_translations: list[str] | None = Field(
        default=None,
        alias="nameTranslations",
        json_schema_extra={"x-go-name": "NameTranslations"},
    )
    networks: list[Company] | None = None
    nominations: list[AwardNomineeBaseRecord] | None = Field(default=None, json_schema_extra={"x-go-name": "Nominees"})
    number: int | None = None
    overview: str | None = None
    overview_translations: list[str] | None = Field(
        default=None,
        alias="overviewTranslations",
        json_schema_extra={"x-go-name": "OverviewTranslations"},
    )
    production_code: str | None = Field(default=None, alias="productionCode")
    remote_ids: list[RemoteID] | None = Field(
        default=None, alias="remoteIds", json_schema_extra={"x-go-name": "RemoteIDs"}
    )
    runtime: int | None = None
    season_number: int | None = Field(default=None, alias="seasonNumber")
    seasons: list[SeasonBaseRecord] | None = Field(default=None, json_schema_extra={"x-go-name": "Seasons"})
    series_id: int | None = Field(default=None, alias="seriesId", json_schema_extra={"x-go-name": "SeriesID"})
    studios: list[Company] | None = None
    tag_options: list[TagOption] | None = Field(
        default=None, alias="tagOptions", json_schema_extra={"x-go-name": "TagOptions"}
    )
    trailers: list[Trailer] | None = Field(default=None, json_schema_extra={"x-go-name": "Trailers"})
    translations: TranslationExtended | None = None
    year: str | None = None


class SearchByRemoteIdResult(BaseModel):
    series: SeriesBaseRecord | None = None
    people: PeopleBaseRecord | None = None
    movie: MovieBaseRecord | None = None
    episode: EpisodeBaseRecord | None = None
    company: Company | None = None


class AwardCategoryExtendedRecord(BaseModel):
    allow_co_nominees: bool | None = Field(
        default=None,
        alias="allowCoNominees",
        json_schema_extra={"x-go-name": "AllowCoNominees"},
    )
    award: AwardBaseRecord | None = None
    for_movies: bool | None = Field(default=None, alias="forMovies", json_schema_extra={"x-go-name": "ForMovies"})
    for_series: bool | None = Field(default=None, alias="forSeries", json_schema_extra={"x-go-name": "ForSeries"})
    id: int | None = Field(default=None, json_schema_extra={"x-go-name": "ID"})
    name: str | None = None
    nominees: list[AwardNomineeBaseRecord] | None = Field(default=None, json_schema_extra={"x-go-name": "Nominees"})
