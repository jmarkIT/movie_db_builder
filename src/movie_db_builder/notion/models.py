from pydantic import BaseModel
from enum import Enum


class NotionPage(BaseModel):
    object: str
    id: str
    created_time: str
    last_edited_time: str
    created_by: str
    last_edited_by: str
    properties: list[NotionProperty]
    url: str


class NotionProperty(BaseModel):
    id: str
    type: NotionPropertyType

    title: str | None = None
    rich_text: str | None = None
    number: int | None = None
    checkbox: bool | None = None
    select: NotionSelectProperty | None = None
    multi_select: list[NotionSelectProperty] | None = None
    people: NotionPerson | None = None
    date: NotionDate | None = None
    relation: list[NotionRelation] | None = None


class NotionPropertyType(str, Enum):
    title = "title"
    rich_text = "rich_text"
    number = "number"
    checkbox = "checkbox"
    select = "select"
    multi_select = "multi_select"
    url = "url"
    formula = "formula"
    rollup = "rollup"
    relation = "relation"
    people = "people"
    created_by = "created_by"
    created_time = "created_time"
    last_edited_by = "last_edited_by"
    last_edited_time = "last_edited_time"
    date = "date"
    email = "email"
    files = "files"
    phone_number = "phone_number"
    place = "place"
    status = "status"


class NotionSelectProperty(BaseModel):
    id: str | None = None
    name: str
    color: str


class NotionPerson(BaseModel):
    object: str
    id: str
    name: str
    type: NotionPeopleType
    person: dict[str, str]


class NotionPeopleType(str, Enum):
    person = "person"


class NotionDate(BaseModel):
    start: str
    end: str


class NotionRelation(BaseModel):
    id: str


class NotionDatabaseQueryResponse(BaseModel):
    object: str
    results: list[NotionPage]
    next_cursor: str | None = None
    has_more: bool
    type: str | None = None
    page: dict[str, str] | None = None


class NotionDatabaseQueryBody(BaseModel):
    start_cursor: str | None = None
