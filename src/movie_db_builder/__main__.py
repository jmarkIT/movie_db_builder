import os

import typer
from sqlalchemy import create_engine

from movie_db_builder.db.db import (
    create_db,
)
from movie_db_builder.notion.notion_client import NotionClient
from movie_db_builder.notion.notion_config import NotionConfig
from movie_db_builder.tmdb.tmdb_client import TMDBClient
from movie_db_builder.tmdb.tmdb_config import TMDBConfig

app = typer.Typer()


@app.command()
def main(file: str) -> None:
    engine = create_engine("sqlite:///movies.db")
    create_db(engine)

    TMDB_TOKEN = os.getenv("TMDB_TOKEN")
    if not TMDB_TOKEN:
        print("tmdb API Token not set")
        raise typer.Exit(code=1)
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    if not NOTION_TOKEN:
        print("notion API Token not set")
        raise typer.Exit(code=1)

    tmdb_config = TMDBConfig(api_token=TMDB_TOKEN)
    tmdb_client = TMDBClient(config=tmdb_config)

    notion_config = NotionConfig(notion_api_key=NOTION_TOKEN)
    notion_client = NotionClient(config=notion_config)

    # # Call api to get list of genres
    # tmdb_genres = tmdb_client.get_genres()

    # # Get tmdb ids from file
    # tmdb_ids: list[str] = []
    # with open(file, "r") as file:
    #     for line in file:
    #         tmdb_ids.append(line.strip())

    # # Call TMDB api for movie details
    # tmdb_movies: list[TMDBMovie] = []
    # for tmdb_id in tmdb_ids:
    #     tmdb_movie = tmdb_client.get_movie_details(
    #         tmdb_id, append_to_response=["credits"]
    #     )
    #     tmdb_movies.append(tmdb_movie)

    # # Add Movies to database
    # add_tmdb_movies(engine=engine, tmdb_movies=tmdb_movies)

    # # Add genres to database
    # add_tmdb_genres(engine=engine, tmdb_genres=tmdb_genres)

    # # Add relationship between movies and genres to database
    # add_tmdb_movie_to_genre(engine=engine, tmdb_movies=tmdb_movies)

    # # Add credits to database
    # add_tmdb_credits(engine=engine, tmdb_movies=tmdb_movies)

    # # Add relationship between movies and credits to database
    # add_tmdb_movie_to_person(engine=engine, tmdb_movies=tmdb_movies)

    _ = notion_client.get_datasource_rows("9d9e132b-5b77-496f-b78b-3c0abd33d1f2")


if __name__ == "__main__":
    app()
