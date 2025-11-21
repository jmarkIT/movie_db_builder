from sqlalchemy import Engine
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session
from sqlalchemy import Insert

from movie_db_builder.db.models import (
    Base,
    Genre,
    Movie,
    MovieToGenre,
    Person,
    MovieToPerson,
)
from movie_db_builder.tmdb.models import TMDBMovie, TMDBGenre


def create_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def add_tmdb_movies(engine: Engine, tmdb_movies: list[TMDBMovie]) -> None:
    with Session(engine) as session:
        stmt: Insert = insert(Movie).values(
            [
                dict(
                    id=m.id,
                    title=m.title,
                    budget=m.budget,
                    revenue=m.revenue,
                    runtime=m.runtime,
                )
                for m in tmdb_movies
            ]
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "budget": stmt.excluded.budget,
                "revenue": stmt.excluded.revenue,
                "runtime": stmt.excluded.runtime,
            },
        )
        session.execute(stmt)
        session.commit()


def add_tmdb_genres(engine: Engine, tmdb_genres: list[TMDBGenre]) -> None:
    with Session(engine) as session:
        stmt: Insert = insert(Genre).values(
            [dict(id=g.id, name=g.name) for g in tmdb_genres]
        )
        stmt: Insert = stmt.on_conflict_do_nothing(index_elements=["id"])
        session.execute(stmt)
        session.commit()


def add_tmdb_movie_to_genre(engine: Engine, tmdb_movies: list[TMDBMovie]) -> None:
    with Session(engine) as session:
        movie_genre_values: list[dict[str, int]] = [
            {"movie_id": movie.id, "genre_id": genre.id}
            for movie in tmdb_movies
            for genre in movie.genres
        ]

        if movie_genre_values:
            stmt: Insert = insert(MovieToGenre).values(movie_genre_values)
            stmt: Insert = stmt.on_conflict_do_nothing()
            session.execute(stmt)
            session.commit()


def add_tmdb_credits(engine: Engine, tmdb_movies: list[TMDBMovie]) -> None:
    with Session(engine) as session:
        # Insert cast
        stmt: Insert = insert(Person).values(
            [
                dict(
                    id=person.id,
                    name=person.name,
                    gender=person.gender,
                    known_for_department=person.known_for_department,
                )
                for movie in tmdb_movies
                for person in movie.credits.cast
            ]
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
        session.execute(stmt)
        session.commit()

        # Insert crew
        stmt = insert(Person).values(
            [
                dict(
                    id=person.id,
                    name=person.name,
                    gender=person.gender,
                    known_for_department=person.known_for_department,
                )
                for movie in tmdb_movies
                for person in movie.credits.crew
            ]
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
        session.execute(stmt)
        session.commit()


def add_tmdb_movie_to_person(engine: Engine, tmdb_movies: list[TMDBMovie]) -> None:
    with Session(engine) as session:
        # Insert cast
        stmt: Insert = insert(MovieToPerson).values(
            [
                dict(
                    movie_id=movie.id,
                    person_id=person.id,
                    cast_id=person.cast_id,
                    credit_id=person.credit_id,
                    character=person.character,
                    order=person.order,
                    department=person.department,
                    job=person.job,
                )
                for movie in tmdb_movies
                for person in movie.credits.cast
            ]
        )
        stmt = stmt.on_conflict_do_nothing()
        session.execute(stmt)
        session.commit()

        # Insert crew
        stmt = insert(MovieToPerson).values(
            [
                dict(
                    movie_id=movie.id,
                    person_id=person.id,
                    cast_id=person.cast_id,
                    credit_id=person.credit_id,
                    character=person.character,
                    order=person.order,
                    department=person.department,
                    job=person.job,
                )
                for movie in tmdb_movies
                for person in movie.credits.crew
            ]
        )
        stmt = stmt.on_conflict_do_nothing()
        session.execute(stmt)
        session.commit()
