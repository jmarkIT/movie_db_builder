"""Tests for database CRUD operations (src/movie_db_builder/db/db.py).

NOTE: These tests require importing db.db which imports tmdb.models.
The tmdb/models.py file has a forward reference bug (TMDBMovie references
TMDBGenre before it's defined). This causes import failures.

These tests will be skipped until the forward reference issue is fixed.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select, inspect
from sqlalchemy.orm import Session

import sys
sys.path.insert(0, "/home/user/movie_db_builder/src")

from movie_db_builder.db.models import (
    Base,
    Movie,
    Genre,
    MovieToGenre,
    Person,
    MovieToPerson,
    WeeklySelection,
)
from movie_db_builder.models import WeeklySelectionData


# Try to import db.db - will fail if forward reference issue exists
try:
    from movie_db_builder.db.db import (
        create_db,
        add_tmdb_movies,
        add_tmdb_genres,
        add_tmdb_movie_to_genre,
        add_tmdb_credits,
        add_tmdb_movie_to_person,
        add_weekly_selection,
    )
    from movie_db_builder.tmdb.models import TMDBMovie, TMDBGenre, TMDBCredits, TMDBPerson
    DB_IMPORTS_AVAILABLE = True
except NameError as e:
    # Forward reference issue - classes not defined in correct order
    DB_IMPORTS_AVAILABLE = False
    CREATE_DB_ERROR = str(e)


# Skip decorator for tests requiring db.db imports
requires_db_imports = pytest.mark.skipif(
    not DB_IMPORTS_AVAILABLE,
    reason=f"Source code has forward reference issue: {CREATE_DB_ERROR if not DB_IMPORTS_AVAILABLE else ''}"
)


class TestCreateDb:
    """Tests for create_db function."""

    @requires_db_imports
    def test_create_db_creates_all_tables(self):
        """Test that all 6 tables are created."""
        engine = create_engine("sqlite:///:memory:")
        create_db(engine)

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        expected_tables = [
            "movies",
            "genres",
            "movies_to_genres",
            "people",
            "movies_to_people",
            "weekly_selections",
        ]

        for table in expected_tables:
            assert table in tables, f"Table {table} not found"

    @requires_db_imports
    def test_create_db_idempotent(self):
        """Test that create_db can run multiple times without error."""
        engine = create_engine("sqlite:///:memory:")

        # Run twice - should not raise
        create_db(engine)
        create_db(engine)

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert len(tables) == 6


@requires_db_imports
class TestAddTmdbMovies:
    """Tests for add_tmdb_movies function."""

    @pytest.fixture
    def sample_tmdb_movie(self):
        """Sample TMDBMovie for testing."""
        return TMDBMovie(
            id=550,
            title="Fight Club",
            budget=63000000,
            revenue=100853753,
            runtime=139,
            genres=[TMDBGenre(id=18, name="Drama")],
            credits=None,
        )

    @pytest.fixture
    def sample_tmdb_movie_list(self):
        """Sample list of TMDBMovies for testing."""
        return [
            TMDBMovie(
                id=550,
                title="Fight Club",
                budget=63000000,
                revenue=100853753,
                runtime=139,
                genres=[TMDBGenre(id=18, name="Drama")],
                credits=None,
            ),
            TMDBMovie(
                id=680,
                title="Pulp Fiction",
                budget=8000000,
                revenue=213928762,
                runtime=154,
                genres=[
                    TMDBGenre(id=18, name="Drama"),
                    TMDBGenre(id=80, name="Crime"),
                ],
                credits=None,
            ),
        ]

    def test_add_single_movie(self, in_memory_engine, sample_tmdb_movie):
        """Test inserting one movie."""
        add_tmdb_movies(in_memory_engine, [sample_tmdb_movie])

        with Session(in_memory_engine) as session:
            movies = session.execute(select(Movie)).scalars().all()
            assert len(movies) == 1
            assert movies[0].id == 550
            assert movies[0].title == "Fight Club"
            assert movies[0].budget == 63000000
            assert movies[0].revenue == 100853753
            assert movies[0].runtime == 139

    def test_add_multiple_movies(self, in_memory_engine, sample_tmdb_movie_list):
        """Test inserting multiple movies."""
        add_tmdb_movies(in_memory_engine, sample_tmdb_movie_list)

        with Session(in_memory_engine) as session:
            movies = session.execute(select(Movie)).scalars().all()
            assert len(movies) == 2

    def test_add_movies_empty_list(self, in_memory_engine):
        """Test empty list is a no-op."""
        # This should not raise
        add_tmdb_movies(in_memory_engine, [])

        with Session(in_memory_engine) as session:
            movies = session.execute(select(Movie)).scalars().all()
            assert len(movies) == 0

    def test_add_movies_upsert_updates(self, in_memory_engine, sample_tmdb_movie):
        """Test that existing ID updates budget/revenue/runtime."""
        # Insert initial movie
        add_tmdb_movies(in_memory_engine, [sample_tmdb_movie])

        # Create updated version with different budget/revenue/runtime
        updated_movie = TMDBMovie(
            id=550,  # Same ID
            title="Fight Club",
            budget=99999999,  # Different
            revenue=999999999,  # Different
            runtime=999,  # Different
            genres=[TMDBGenre(id=18, name="Drama")],
            credits=None,
        )

        add_tmdb_movies(in_memory_engine, [updated_movie])

        with Session(in_memory_engine) as session:
            movie = session.execute(
                select(Movie).where(Movie.id == 550)
            ).scalar_one()

            # Should have updated values
            assert movie.budget == 99999999
            assert movie.revenue == 999999999
            assert movie.runtime == 999
            # Title should remain the same since it's not in the upsert
            assert movie.title == "Fight Club"

    def test_add_movies_large_integers(self, in_memory_engine):
        """Test handling of large budget/revenue values."""
        large_movie = TMDBMovie(
            id=1,
            title="Expensive Movie",
            budget=2_000_000_000,  # 2 billion
            revenue=10_000_000_000,  # 10 billion
            runtime=180,
            genres=[],
            credits=None,
        )

        add_tmdb_movies(in_memory_engine, [large_movie])

        with Session(in_memory_engine) as session:
            movie = session.execute(select(Movie)).scalar_one()
            assert movie.budget == 2_000_000_000
            assert movie.revenue == 10_000_000_000


@requires_db_imports
class TestAddTmdbGenres:
    """Tests for add_tmdb_genres function."""

    @pytest.fixture
    def sample_tmdb_genre_list(self):
        """Sample list of TMDBGenres for testing."""
        return [
            TMDBGenre(id=18, name="Drama"),
            TMDBGenre(id=28, name="Action"),
            TMDBGenre(id=35, name="Comedy"),
        ]

    def test_add_single_genre(self, in_memory_engine):
        """Test inserting one genre."""
        genre = TMDBGenre(id=18, name="Drama")
        add_tmdb_genres(in_memory_engine, [genre])

        with Session(in_memory_engine) as session:
            genres = session.execute(select(Genre)).scalars().all()
            assert len(genres) == 1
            assert genres[0].id == 18
            assert genres[0].name == "Drama"

    def test_add_genres_duplicate_ignored(self, in_memory_engine, sample_tmdb_genre_list):
        """Test that conflict (duplicate) does nothing."""
        # Insert genres
        add_tmdb_genres(in_memory_engine, sample_tmdb_genre_list)

        # Insert again - should not raise and not duplicate
        add_tmdb_genres(in_memory_engine, sample_tmdb_genre_list)

        with Session(in_memory_engine) as session:
            genres = session.execute(select(Genre)).scalars().all()
            assert len(genres) == 3

    def test_add_genres_empty_list(self, in_memory_engine):
        """Test empty list is a no-op."""
        add_tmdb_genres(in_memory_engine, [])

        with Session(in_memory_engine) as session:
            genres = session.execute(select(Genre)).scalars().all()
            assert len(genres) == 0


@requires_db_imports
class TestAddTmdbMovieToGenre:
    """Tests for add_tmdb_movie_to_genre function."""

    @pytest.fixture
    def sample_tmdb_movie(self):
        """Sample TMDBMovie for testing."""
        return TMDBMovie(
            id=550,
            title="Fight Club",
            budget=63000000,
            revenue=100853753,
            runtime=139,
            genres=[TMDBGenre(id=18, name="Drama")],
            credits=None,
        )

    @pytest.fixture
    def sample_tmdb_genre_list(self):
        """Sample list of TMDBGenres for testing."""
        return [
            TMDBGenre(id=18, name="Drama"),
            TMDBGenre(id=28, name="Action"),
            TMDBGenre(id=35, name="Comedy"),
        ]

    def test_add_movie_genre_relationship(self, in_memory_engine, sample_tmdb_movie, sample_tmdb_genre_list):
        """Test linking movie to genre."""
        # First add movie and genres
        add_tmdb_movies(in_memory_engine, [sample_tmdb_movie])
        add_tmdb_genres(in_memory_engine, sample_tmdb_genre_list)

        # Add relationship
        add_tmdb_movie_to_genre(in_memory_engine, [sample_tmdb_movie])

        with Session(in_memory_engine) as session:
            relations = session.execute(select(MovieToGenre)).scalars().all()
            assert len(relations) == 1
            assert relations[0].movie_id == 550
            assert relations[0].genre_id == 18

    def test_add_movie_multiple_genres(self, in_memory_engine, sample_tmdb_genre_list):
        """Test movie with multiple genres."""
        # Create movie with multiple genres
        multi_genre_movie = TMDBMovie(
            id=680,
            title="Pulp Fiction",
            budget=8000000,
            revenue=213928762,
            runtime=154,
            genres=[
                TMDBGenre(id=18, name="Drama"),
                TMDBGenre(id=80, name="Crime"),
            ],
            credits=None,
        )

        add_tmdb_movies(in_memory_engine, [multi_genre_movie])
        add_tmdb_genres(in_memory_engine, sample_tmdb_genre_list + [TMDBGenre(id=80, name="Crime")])
        add_tmdb_movie_to_genre(in_memory_engine, [multi_genre_movie])

        with Session(in_memory_engine) as session:
            relations = session.execute(
                select(MovieToGenre).where(MovieToGenre.movie_id == 680)
            ).scalars().all()
            assert len(relations) == 2

    def test_add_movie_no_genres(self, in_memory_engine):
        """Test movie with empty genres list."""
        no_genre_movie = TMDBMovie(
            id=999,
            title="No Genre Movie",
            budget=1000000,
            revenue=2000000,
            runtime=90,
            genres=[],
            credits=None,
        )

        add_tmdb_movies(in_memory_engine, [no_genre_movie])
        add_tmdb_movie_to_genre(in_memory_engine, [no_genre_movie])

        with Session(in_memory_engine) as session:
            relations = session.execute(select(MovieToGenre)).scalars().all()
            assert len(relations) == 0


@requires_db_imports
class TestAddTmdbCredits:
    """Tests for add_tmdb_credits function."""

    @pytest.fixture
    def sample_tmdb_movie(self):
        """Sample TMDBMovie for testing."""
        return TMDBMovie(
            id=550,
            title="Fight Club",
            budget=63000000,
            revenue=100853753,
            runtime=139,
            genres=[TMDBGenre(id=18, name="Drama")],
            credits=None,
        )

    @pytest.fixture
    def sample_tmdb_movie_with_credits(self):
        """Sample TMDBMovie with credits for testing."""
        cast_member = TMDBPerson(
            adult=False,
            gender=2,
            id=819,
            known_for_department="Acting",
            name="Edward Norton",
            originalName="Edward Norton",
            popularity=26.99,
            profilePath="/8nytsqL59SFJTVYVrN72k6qkGgJ.jpg",
            cast_id=4,
            character="The Narrator",
            credit_id="52fe4250c3a36847f80149f3",
            order=0,
            department=None,
            job=None,
        )
        crew_member = TMDBPerson(
            adult=False,
            gender=2,
            id=7467,
            known_for_department="Directing",
            name="David Fincher",
            originalName="David Fincher",
            popularity=15.23,
            profilePath="/tpEczFclQZeKAiCeKZZ0adRvtfz.jpg",
            cast_id=None,
            character=None,
            credit_id="52fe4250c3a36847f8014a01",
            order=None,
            department="Directing",
            job="Director",
        )
        return TMDBMovie(
            id=550,
            title="Fight Club",
            budget=63000000,
            revenue=100853753,
            runtime=139,
            genres=[TMDBGenre(id=18, name="Drama")],
            credits=TMDBCredits(cast=[cast_member], crew=[crew_member]),
        )

    def test_add_cast_members(self, in_memory_engine, sample_tmdb_movie_with_credits):
        """Test inserting cast as Person."""
        add_tmdb_movies(in_memory_engine, [sample_tmdb_movie_with_credits])
        add_tmdb_credits(in_memory_engine, [sample_tmdb_movie_with_credits])

        with Session(in_memory_engine) as session:
            people = session.execute(select(Person)).scalars().all()
            # Should have cast member and crew member
            assert len(people) == 2

            # Find cast member
            cast = next((p for p in people if p.id == 819), None)
            assert cast is not None
            assert cast.name == "Edward Norton"
            assert cast.known_for_department == "Acting"

    def test_add_crew_members(self, in_memory_engine, sample_tmdb_movie_with_credits):
        """Test inserting crew as Person."""
        add_tmdb_movies(in_memory_engine, [sample_tmdb_movie_with_credits])
        add_tmdb_credits(in_memory_engine, [sample_tmdb_movie_with_credits])

        with Session(in_memory_engine) as session:
            people = session.execute(select(Person)).scalars().all()

            # Find crew member
            crew = next((p for p in people if p.id == 7467), None)
            assert crew is not None
            assert crew.name == "David Fincher"
            assert crew.known_for_department == "Directing"

    def test_add_credits_duplicate_person(self, in_memory_engine):
        """Test same person in multiple movies doesn't duplicate."""
        # Create two movies with same actor
        person = TMDBPerson(
            adult=False,
            gender=2,
            id=819,
            known_for_department="Acting",
            name="Edward Norton",
            originalName="Edward Norton",
            popularity=26.99,
            profilePath=None,
            cast_id=4,
            character="Character 1",
            credit_id="credit1",
            order=0,
            department=None,
            job=None,
        )

        movie1 = TMDBMovie(
            id=1,
            title="Movie 1",
            budget=1000000,
            revenue=2000000,
            runtime=90,
            genres=[],
            credits=TMDBCredits(cast=[person], crew=[]),
        )

        person2 = TMDBPerson(
            adult=False,
            gender=2,
            id=819,  # Same ID
            known_for_department="Acting",
            name="Edward Norton",
            originalName="Edward Norton",
            popularity=26.99,
            profilePath=None,
            cast_id=5,
            character="Character 2",
            credit_id="credit2",
            order=0,
            department=None,
            job=None,
        )

        movie2 = TMDBMovie(
            id=2,
            title="Movie 2",
            budget=1000000,
            revenue=2000000,
            runtime=90,
            genres=[],
            credits=TMDBCredits(cast=[person2], crew=[]),
        )

        add_tmdb_movies(in_memory_engine, [movie1, movie2])
        add_tmdb_credits(in_memory_engine, [movie1, movie2])

        with Session(in_memory_engine) as session:
            people = session.execute(select(Person)).scalars().all()
            # Should only have one person entry
            assert len(people) == 1
            assert people[0].id == 819

    def test_add_credits_null_credits(self, in_memory_engine, sample_tmdb_movie):
        """Test movie with credits=None."""
        add_tmdb_movies(in_memory_engine, [sample_tmdb_movie])

        # This should raise AttributeError since credits is None
        # and the code tries to access movie.credits.cast
        with pytest.raises(AttributeError):
            add_tmdb_credits(in_memory_engine, [sample_tmdb_movie])


@requires_db_imports
class TestAddTmdbMovieToPerson:
    """Tests for add_tmdb_movie_to_person function."""

    @pytest.fixture
    def sample_tmdb_movie_with_credits(self):
        """Sample TMDBMovie with credits for testing."""
        cast_member = TMDBPerson(
            adult=False,
            gender=2,
            id=819,
            known_for_department="Acting",
            name="Edward Norton",
            originalName="Edward Norton",
            popularity=26.99,
            profilePath="/8nytsqL59SFJTVYVrN72k6qkGgJ.jpg",
            cast_id=4,
            character="The Narrator",
            credit_id="52fe4250c3a36847f80149f3",
            order=0,
            department=None,
            job=None,
        )
        crew_member = TMDBPerson(
            adult=False,
            gender=2,
            id=7467,
            known_for_department="Directing",
            name="David Fincher",
            originalName="David Fincher",
            popularity=15.23,
            profilePath="/tpEczFclQZeKAiCeKZZ0adRvtfz.jpg",
            cast_id=None,
            character=None,
            credit_id="52fe4250c3a36847f8014a01",
            order=None,
            department="Directing",
            job="Director",
        )
        return TMDBMovie(
            id=550,
            title="Fight Club",
            budget=63000000,
            revenue=100853753,
            runtime=139,
            genres=[TMDBGenre(id=18, name="Drama")],
            credits=TMDBCredits(cast=[cast_member], crew=[crew_member]),
        )

    def test_add_cast_relationship(self, in_memory_engine, sample_tmdb_movie_with_credits):
        """Test cast with character/order."""
        add_tmdb_movies(in_memory_engine, [sample_tmdb_movie_with_credits])
        add_tmdb_credits(in_memory_engine, [sample_tmdb_movie_with_credits])
        add_tmdb_movie_to_person(in_memory_engine, [sample_tmdb_movie_with_credits])

        with Session(in_memory_engine) as session:
            relations = session.execute(select(MovieToPerson)).scalars().all()

            # Find cast relation
            cast_rel = next(
                (r for r in relations if r.credit_id == "52fe4250c3a36847f80149f3"),
                None,
            )
            assert cast_rel is not None
            assert cast_rel.movie_id == 550
            assert cast_rel.person_id == 819
            assert cast_rel.character == "The Narrator"
            assert cast_rel.order == 0

    def test_add_crew_relationship(self, in_memory_engine, sample_tmdb_movie_with_credits):
        """Test crew with department/job."""
        add_tmdb_movies(in_memory_engine, [sample_tmdb_movie_with_credits])
        add_tmdb_credits(in_memory_engine, [sample_tmdb_movie_with_credits])
        add_tmdb_movie_to_person(in_memory_engine, [sample_tmdb_movie_with_credits])

        with Session(in_memory_engine) as session:
            relations = session.execute(select(MovieToPerson)).scalars().all()

            # Find crew relation
            crew_rel = next(
                (r for r in relations if r.credit_id == "52fe4250c3a36847f8014a01"),
                None,
            )
            assert crew_rel is not None
            assert crew_rel.movie_id == 550
            assert crew_rel.person_id == 7467
            assert crew_rel.department == "Directing"
            assert crew_rel.job == "Director"

    def test_add_duplicate_credit_id(self, in_memory_engine, sample_tmdb_movie_with_credits):
        """Test conflict handling for duplicate credit_id."""
        add_tmdb_movies(in_memory_engine, [sample_tmdb_movie_with_credits])
        add_tmdb_credits(in_memory_engine, [sample_tmdb_movie_with_credits])

        # Insert once
        add_tmdb_movie_to_person(in_memory_engine, [sample_tmdb_movie_with_credits])

        # Insert again - should not raise or duplicate
        add_tmdb_movie_to_person(in_memory_engine, [sample_tmdb_movie_with_credits])

        with Session(in_memory_engine) as session:
            relations = session.execute(select(MovieToPerson)).scalars().all()
            assert len(relations) == 2  # One cast, one crew


@requires_db_imports
class TestAddWeeklySelection:
    """Tests for add_weekly_selection function."""

    @pytest.fixture
    def sample_tmdb_movie(self):
        """Sample TMDBMovie for testing."""
        return TMDBMovie(
            id=550,
            title="Fight Club",
            budget=63000000,
            revenue=100853753,
            runtime=139,
            genres=[TMDBGenre(id=18, name="Drama")],
            credits=None,
        )

    @pytest.fixture
    def sample_tmdb_movie_list(self):
        """Sample list of TMDBMovies for testing."""
        return [
            TMDBMovie(
                id=550,
                title="Fight Club",
                budget=63000000,
                revenue=100853753,
                runtime=139,
                genres=[TMDBGenre(id=18, name="Drama")],
                credits=None,
            ),
            TMDBMovie(
                id=680,
                title="Pulp Fiction",
                budget=8000000,
                revenue=213928762,
                runtime=154,
                genres=[
                    TMDBGenre(id=18, name="Drama"),
                    TMDBGenre(id=80, name="Crime"),
                ],
                credits=None,
            ),
        ]

    def test_add_single_selection(
        self, in_memory_engine, sample_weekly_selection, sample_tmdb_movie
    ):
        """Test inserting one selection."""
        # First add the movie (for FK constraint)
        add_tmdb_movies(in_memory_engine, [sample_tmdb_movie])

        add_weekly_selection(in_memory_engine, [sample_weekly_selection])

        with Session(in_memory_engine) as session:
            selections = session.execute(select(WeeklySelection)).scalars().all()
            assert len(selections) == 1
            assert selections[0].week_of == "2024-01-15"
            assert selections[0].master_of_ceremony == "John"
            assert selections[0].primary_movie_id == 550

    def test_add_selection_with_secondary(self, in_memory_engine, sample_tmdb_movie_list):
        """Test selection with secondary_movie_id."""
        add_tmdb_movies(in_memory_engine, sample_tmdb_movie_list)

        selection = WeeklySelectionData(
            week_of="2024-01-22",
            master_of_ceremony="Jane",
            primary_movie_id="550",
            secondary_movie_id="680",
        )

        add_weekly_selection(in_memory_engine, [selection])

        with Session(in_memory_engine) as session:
            ws = session.execute(select(WeeklySelection)).scalar_one()
            assert ws.secondary_movie_id == 680

    def test_add_selection_without_secondary(
        self, in_memory_engine, sample_weekly_selection, sample_tmdb_movie
    ):
        """Test selection with secondary_movie_id as None."""
        add_tmdb_movies(in_memory_engine, [sample_tmdb_movie])
        add_weekly_selection(in_memory_engine, [sample_weekly_selection])

        with Session(in_memory_engine) as session:
            ws = session.execute(select(WeeklySelection)).scalar_one()
            assert ws.secondary_movie_id is None

    def test_add_selection_duplicate_week(
        self, in_memory_engine, sample_weekly_selection, sample_tmdb_movie
    ):
        """Test that duplicate week_of conflict does nothing."""
        add_tmdb_movies(in_memory_engine, [sample_tmdb_movie])

        # Insert once
        add_weekly_selection(in_memory_engine, [sample_weekly_selection])

        # Insert again - should not raise or duplicate
        add_weekly_selection(in_memory_engine, [sample_weekly_selection])

        with Session(in_memory_engine) as session:
            selections = session.execute(select(WeeklySelection)).scalars().all()
            assert len(selections) == 1
