from movie_db_builder.db.models import WeeklySelection
from movie_db_builder.notion.notion_client import NotionClient
from movie_db_builder.notion.models import NotionPage
from movie_db_builder.models import WeeklySelectionData

from typing import cast


def extract_movie_pages(week: NotionPage, client: NotionClient) -> list[NotionPage]:
    movie_pages: list[NotionPage] = []
    relations = week.properties["Movie"].relation
    if relations is None:
        raise TypeError("Missing relations")
    movie_page_1_id = relations[0].id
    movie_page_1 = client.get_page(page_id=movie_page_1_id)
    movie_pages.append(movie_page_1)
    if relations.count == 2:
        movie_page_2_id = relations[1].id
        movie_page_2 = client.get_page(page_id=movie_page_2_id)
        movie_pages.append(movie_page_2)
    return movie_pages


def build_weekly_selections(
    week: NotionPage, movies: list[NotionPage]
) -> WeeklySelectionData:
    week_of = week.properties["Week of"].date.start
    movie_id_1 = cast(str, movies[0].properties["TMDB ID"].plain_text)
    movie_id_2 = None
    if movies.count == 2:
        movie_id_2 = movies[1].properties["TMDB ID"].plain_text
    master_of_ceremony = week.properties["Master of Ceremony"].select.name
    return WeeklySelectionData(
        week_of=week_of,
        master_of_ceremony=master_of_ceremony,
        primary_movie_id=movie_id_1,
        secondary_movie_id=movie_id_2,
    )
