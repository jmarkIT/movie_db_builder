import os

from sqlalchemy import create_engine

from movie_db_builder.db.db import (
    create_db,
    add_tmdb_movies,
    add_tmdb_genres,
    add_tmdb_movie_to_genre,
    add_tmdb_credits,
    add_tmdb_movie_to_person,
)
from movie_db_builder.tmdb.models import TMDBMovie, TMDBGenre
from movie_db_builder.tmdb.tmdb_client import TMDBClient
from movie_db_builder.tmdb.tmdb_config import TMDBConfig


def main():
    engine = create_engine("sqlite:///movies.db")
    create_db(engine)
    TMDB_TOKEN = os.getenv("TMDB_TOKEN")
    if not TMDB_TOKEN:
        print("tmdb API Token not set")
        exit(1)
    config = TMDBConfig(api_token=TMDB_TOKEN)
    client = TMDBClient(config=config)

    # Call api to get list of genres
    tmdb_genres = client.get_genres()

    # Get tmdb ids from file
    tmdb_ids: list[str] = []
    with open("../tmdb.csv", "r") as file:
        for line in file:
            tmdb_ids.append(line.strip())

    # Call TMDB api for movie details
    tmdb_movies: list[TMDBMovie] = []
    for tmdb_id in tmdb_ids:
        tmdb_movie = client.get_movie_details(tmdb_id, append_to_response=["credits"])
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


if __name__ == "__main__":
    main()
