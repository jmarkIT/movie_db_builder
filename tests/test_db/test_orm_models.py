"""Tests for SQLAlchemy ORM models (src/movie_db_builder/db/models.py)."""

import pytest

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


class TestMovieModel:
    """Tests for Movie ORM model."""

    def test_movie_creation(self):
        """Test Movie ORM object instantiation."""
        movie = Movie(
            id=550,
            title="Fight Club",
            budget=63000000,
            revenue=100853753,
            runtime=139,
        )
        assert movie.id == 550
        assert movie.title == "Fight Club"
        assert movie.budget == 63000000
        assert movie.revenue == 100853753
        assert movie.runtime == 139

    def test_movie_repr(self):
        """Test __repr__ format - should have '=' signs."""
        movie = Movie(
            id=550,
            title="Fight Club",
            budget=63000000,
            revenue=100853753,
            runtime=139,
        )
        repr_str = repr(movie)
        # The test documents the bug: title{ instead of title={
        # This test will FAIL due to the known bug
        assert "id=550" in repr_str
        assert "title='Fight Club'" in repr_str or "title=\"Fight Club\"" in repr_str

    def test_movie_tablename(self):
        """Test Movie table name."""
        assert Movie.__tablename__ == "movies"


class TestGenreModel:
    """Tests for Genre ORM model."""

    def test_genre_creation(self):
        """Test Genre ORM object instantiation."""
        genre = Genre(id=18, name="Drama")
        assert genre.id == 18
        assert genre.name == "Drama"

    def test_genre_repr(self):
        """Test __repr__ format - should have '=' signs."""
        genre = Genre(id=18, name="Drama")
        repr_str = repr(genre)
        # The test documents the bug: name{ instead of name={
        # Also note: the repr uses 'title' instead of 'name' which is incorrect
        # This test will FAIL due to the known bug
        assert "id=18" in repr_str
        assert "name='Drama'" in repr_str or "name=\"Drama\"" in repr_str

    def test_genre_tablename(self):
        """Test Genre table name."""
        assert Genre.__tablename__ == "genres"


class TestPersonModel:
    """Tests for Person ORM model."""

    def test_person_creation(self):
        """Test Person ORM object instantiation."""
        person = Person(
            id=819,
            name="Edward Norton",
            gender=2,
            known_for_department="Acting",
        )
        assert person.id == 819
        assert person.name == "Edward Norton"
        assert person.gender == 2
        assert person.known_for_department == "Acting"

    def test_person_with_optional_fields(self):
        """Test Person with NULL known_for_department."""
        person = Person(
            id=12345,
            name="Unknown Person",
            gender=0,
            known_for_department=None,
        )
        assert person.known_for_department is None

    def test_person_tablename(self):
        """Test Person table name."""
        assert Person.__tablename__ == "people"


class TestMovieToGenreModel:
    """Tests for MovieToGenre junction table."""

    def test_movie_to_genre_creation(self):
        """Test MovieToGenre junction record."""
        mtg = MovieToGenre(movie_id=550, genre_id=18)
        assert mtg.movie_id == 550
        assert mtg.genre_id == 18

    def test_movie_to_genre_composite_key(self):
        """Test that MovieToGenre has composite primary key."""
        # Check mapper for primary key columns
        pk_columns = [c.name for c in MovieToGenre.__table__.primary_key.columns]
        assert "movie_id" in pk_columns
        assert "genre_id" in pk_columns
        assert len(pk_columns) == 2

    def test_movie_to_genre_tablename(self):
        """Test MovieToGenre table name."""
        assert MovieToGenre.__tablename__ == "movies_to_genres"


class TestMovieToPersonModel:
    """Tests for MovieToPerson junction table."""

    def test_movie_to_person_cast_creation(self):
        """Test MovieToPerson for cast member."""
        mtp = MovieToPerson(
            credit_id="52fe4250c3a36847f80149f3",
            movie_id=550,
            person_id=819,
            cast_id=4,
            character="The Narrator",
            order=0,
            department=None,
            job=None,
        )
        assert mtp.credit_id == "52fe4250c3a36847f80149f3"
        assert mtp.movie_id == 550
        assert mtp.person_id == 819
        assert mtp.cast_id == 4
        assert mtp.character == "The Narrator"
        assert mtp.order == 0
        assert mtp.department is None
        assert mtp.job is None

    def test_movie_to_person_crew_creation(self):
        """Test MovieToPerson for crew member."""
        mtp = MovieToPerson(
            credit_id="52fe4250c3a36847f8014a01",
            movie_id=550,
            person_id=7467,
            cast_id=None,
            character=None,
            order=None,
            department="Directing",
            job="Director",
        )
        assert mtp.credit_id == "52fe4250c3a36847f8014a01"
        assert mtp.department == "Directing"
        assert mtp.job == "Director"

    def test_movie_to_person_credit_id_pk(self):
        """Test that credit_id is primary key."""
        pk_columns = [c.name for c in MovieToPerson.__table__.primary_key.columns]
        assert "credit_id" in pk_columns
        assert len(pk_columns) == 1

    def test_movie_to_person_tablename(self):
        """Test MovieToPerson table name."""
        assert MovieToPerson.__tablename__ == "movies_to_people"


class TestWeeklySelectionModel:
    """Tests for WeeklySelection ORM model."""

    def test_weekly_selection_creation(self):
        """Test WeeklySelection ORM object instantiation."""
        ws = WeeklySelection(
            week_of="2024-01-15",
            master_of_ceremony="John",
            primary_movie_id=550,
            secondary_movie_id=680,
        )
        assert ws.week_of == "2024-01-15"
        assert ws.master_of_ceremony == "John"
        assert ws.primary_movie_id == 550
        assert ws.secondary_movie_id == 680

    def test_weekly_selection_without_secondary(self):
        """Test WeeklySelection with no secondary movie."""
        ws = WeeklySelection(
            week_of="2024-01-15",
            master_of_ceremony="John",
            primary_movie_id=550,
            secondary_movie_id=None,
        )
        assert ws.secondary_movie_id is None

    def test_weekly_selection_fk_constraints(self):
        """Test that foreign keys are defined to Movie table."""
        fks = list(WeeklySelection.__table__.foreign_keys)
        fk_refs = [fk.target_fullname for fk in fks]
        assert "movies.id" in fk_refs
        # Should have two FKs to movies.id (primary and secondary)
        assert fk_refs.count("movies.id") == 2

    def test_weekly_selection_tablename(self):
        """Test WeeklySelection table name."""
        assert WeeklySelection.__tablename__ == "weekly_selections"
