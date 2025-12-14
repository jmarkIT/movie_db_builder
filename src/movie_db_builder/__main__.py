import asyncio
import os
from typing import cast

import typer
from sqlalchemy import create_engine

from movie_db_builder.db.db import (
    add_tmdb_credits,
    add_tmdb_genres,
    add_tmdb_movie_to_genre,
    add_tmdb_movie_to_person,
    add_tmdb_movies,
    add_weekly_selection,
    create_db,
)
from movie_db_builder.models import WeeklySelectionData
from movie_db_builder.music_brainz.music_brainz_client import MusicBrainzClient
from movie_db_builder.music_brainz.music_brainz_config import MusicBrainzConfig
from movie_db_builder.notion.models import NotionPage
from movie_db_builder.notion.notion_client import NotionClient
from movie_db_builder.notion.notion_config import NotionConfig
from movie_db_builder.tmdb.models import TMDBGenre, TMDBMovie
from movie_db_builder.tmdb.tmdb_client import TMDBClient
from movie_db_builder.tmdb.tmdb_config import TMDBConfig
from movie_db_builder.utils import build_weekly_selections, extract_movie_pages

app = typer.Typer()


async def async_main() -> None:
    engine = create_engine("sqlite:///movies.db")
    create_db(engine)

    TMDB_TOKEN: str | None = os.getenv(key="TMDB_TOKEN")
    if TMDB_TOKEN is None:
        print("Please set TMDB_TOKEN environment variable")
        raise typer.Exit(code=1)
    NOTION_TOKEN: str | None = os.getenv(key="NOTION_TOKEN")
    if NOTION_TOKEN is None:
        print("Please set NOTION_TOKEN environment variable")
        raise typer.Exit(code=1)
    MOVIE_DATASOURCE_ID: str | None = os.getenv(key="MOVIE_DATASOURCE_ID")
    if MOVIE_DATASOURCE_ID is None:
        print("Please set MOVIE_DATASOURCE_ID environment variable")
        raise typer.Exit(code=1)
    WEEK_DATASOURCE_ID: str | None = os.getenv(key="WEEK_DATASOURCE_ID")
    if WEEK_DATASOURCE_ID is None:
        print("Please set WEEK_DATASOURCE_ID environment variable")
        raise typer.Exit(code=1)

    tmdb_config = TMDBConfig(api_token=TMDB_TOKEN)
    tmdb_client = TMDBClient(config=tmdb_config)

    notion_config = NotionConfig(notion_api_key=NOTION_TOKEN)
    notion_client = NotionClient(config=notion_config)

    music_brainz_config = MusicBrainzConfig(
        user_agent="movie_db_builder/0.0.1 ( james.david.mark@gmail.com )",
        auth_token="",
    )
    async with MusicBrainzClient(cfg=music_brainz_config) as client:
        release = await client.get_release(
            release_id="aa97e4af-a4a6-4e59-9319-80f7fa64e376"
        )
        print(release)

    # Get all weekly selections from Weekly Selections tabble
    print("Getting weekly selections from Notion...")
    week_rows: list[NotionPage] = notion_client.get_datasource_rows(
        data_source_id=WEEK_DATASOURCE_ID
    )
    print(f"There are {len(week_rows)} week rows found")

    # Build WeeklySelections from week_rows
    print("Building weekly selections...")
    weekly_selections: list[WeeklySelectionData] = []
    for week in week_rows:
        movie_pages = extract_movie_pages(week=week, client=notion_client)
        weekly_selection = build_weekly_selections(week=week, movies=movie_pages)
        weekly_selections.append(weekly_selection)

    print(f"There are {len(weekly_selections)}")
    # Get all movies from the Movies table
    print("Getting movie list from Notion...")
    movie_rows: list[NotionPage] = notion_client.get_datasource_rows(
        data_source_id=MOVIE_DATASOURCE_ID
    )

    # Extract TMDB IDs from the Movies table
    print("Extracting TMDB IDs from Notion data...")
    tmdb_ids = [
        cast(str, movie.properties["TMDB ID"].plain_text) for movie in movie_rows
    ]

    # Call api to get list of genres
    print("Getting list of genres from TMDB...")
    tmdb_genres: list[TMDBGenre] = tmdb_client.get_genres()

    # Call TMDB api for movie details
    tmdb_movies: list[TMDBMovie] = []
    for tmdb_id in tmdb_ids:
        tmdb_movie: TMDBMovie | None = tmdb_client.get_movie_details(
            tmdb_id, append_to_response=["credits"]
        )
        if tmdb_movie is not None:
            tmdb_movies.append(tmdb_movie)

    # Add Movies to database
    add_tmdb_movies(engine=engine, tmdb_movies=tmdb_movies)

    # Add genres to database
    add_tmdb_genres(engine=engine, tmdb_genres=tmdb_genres)

    # Add relationship between movies and genres to database
    add_tmdb_movie_to_genre(engine=engine, tmdb_movies=tmdb_movies)

    # Add credits to database
    add_tmdb_credits(engine=engine, tmdb_movies=tmdb_movies)

    # Add relationship between movies and credits to database
    add_tmdb_movie_to_person(engine=engine, tmdb_movies=tmdb_movies)

    # Add weekly selections
    add_weekly_selection(engine=engine, weekly_selections=weekly_selections)


@app.command()
def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    app()
