from sqlalchemy import Engine
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from movie_db_builder.db.models import (
    Base,
    Genre,
    Movie,
    MovieGenre,
    Person,
    MoviePerson,
)
from movie_db_builder.tmdb.models import TMDBMovie


def create_db(engine: Engine):
    Base.metadata.create_all(engine)


def add_tmdb_movies(engine: Engine, tmdb_movies: list[TMDBMovie]):
    with Session(engine) as session:
        stmt = insert(Movie).values(
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


def add_tmdb_genres(engine: Engine, tmdb_genres: list[TMBDGenre]):
    with Session(engine) as session:
        stmt = insert(Genre).values([dict(id=g.id, name=g.name) for g in tmdb_genres])
        stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
        session.execute(stmt)
        session.commit()


def add_tmdb_movie_genre(engine: Engine, tmdb_movies: list[TMDBMovie]):
    with Session(engine) as session:
        movie_genre_values = [
            {"id": movie.id + genre.id, "movie_id": movie.id, "genre_id": genre.id}
            for movie in tmdb_movies
            for genre in movie.genres
        ]

        if movie_genre_values:
            stmt = insert(MovieGenre).values(movie_genre_values)
            stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
            session.execute(stmt)
            session.commit()


def add_tmdb_credits(engine: Engine, tmdb_movies: list[TMDBMovie]):
    with Session(engine) as session:
        # Insert cast
        stmt = insert(Person).values(
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


def add_tmdb_movie_person(engine: Engine, tmdb_movies: list[TMDBMovie]):
    with Session(engine) as session:
        # Inset cast
        stmt = insert(MoviePerson).values(
            [
                dict(
                    id=person.credit_id,
                    movie_id=movie.id,
                    person_id=person.id,
                    cast_id=person.cast_id,
                    character=person.character,
                    order=person.order,
                    department=person.department,
                    job=person.job,
                )
                for movie in tmdb_movies
                for person in movie.credits.cast
            ]
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
        session.execute(stmt)
        session.commit()

        # Insert crew
        stmt = insert(MoviePerson).values(
            [
                dict(
                    id=int(str(movie.id) + str(person.id)),
                    movie_id=movie.id,
                    person_id=person.id,
                    cast_id=person.cast_id,
                    character=person.character,
                    order=person.order,
                    department=person.department,
                    job=person.job,
                )
                for movie in tmdb_movies
                for person in movie.credits.crew
            ]
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
        session.execute(stmt)
        session.commit()
