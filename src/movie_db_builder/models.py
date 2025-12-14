from pydantic import BaseModel


class WeeklySelectionData(BaseModel):
    week_of: str
    master_of_ceremony: str
    primary_movie_id: str
    secondary_movie_id: str | None = None
