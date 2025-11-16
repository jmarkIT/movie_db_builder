from pydantic import BaseModel


class TMDBMovie(BaseModel):
    id: int
    title: str
    budget: int
    revenue: int
    runtime: int
    genres: list[TMDBGenre]
    credits: TMDBCredits | None = None


class TMDBGenre(BaseModel):
    id: int
    name: str


class TMDBGenresQuery(BaseModel):
    genres: list[TMDBGenre]


class TMDBCredits(BaseModel):
    cast: list[TMDBPerson]
    crew: list[TMDBPerson]


class TMDBPerson(BaseModel):
    adult: bool
    gender: int
    id: int
    known_for_department: str | None = None
    name: str
    originalName: str | None = None
    popularity: float
    profilePath: str | None = None
    cast_id: int | None = None
    character: str | None = None
    credit_id: str
    order: int | None = None
    department: str | None = None
    job: str | None = None
