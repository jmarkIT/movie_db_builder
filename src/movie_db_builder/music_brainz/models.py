from pydantic import BaseModel


class MusicBrainzRelease(BaseModel):
    id: str
    title: str
    date: str
    genres: list[MusicBrainzGenre]


class MusicBrainzGenre(BaseModel):
    id: str
    name: str
