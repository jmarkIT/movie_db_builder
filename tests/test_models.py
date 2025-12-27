"""Tests for core Pydantic models (src/movie_db_builder/models.py)."""

import pytest
from pydantic import ValidationError

import sys
sys.path.insert(0, "/home/user/movie_db_builder/src")

from movie_db_builder.models import WeeklySelectionData


class TestWeeklySelectionData:
    """Tests for WeeklySelectionData model."""

    def test_weekly_selection_data_valid(self):
        """Test WeeklySelectionData with all required fields."""
        selection = WeeklySelectionData(
            week_of="2024-01-15",
            master_of_ceremony="John",
            primary_movie_id="550",
            secondary_movie_id="551",
        )
        assert selection.week_of == "2024-01-15"
        assert selection.master_of_ceremony == "John"
        assert selection.primary_movie_id == "550"
        assert selection.secondary_movie_id == "551"

    def test_weekly_selection_data_optional_secondary(self):
        """Test WeeklySelectionData with secondary_movie_id as None."""
        selection = WeeklySelectionData(
            week_of="2024-01-15",
            master_of_ceremony="Jane",
            primary_movie_id="550",
            secondary_movie_id=None,
        )
        assert selection.secondary_movie_id is None

    def test_weekly_selection_data_default_secondary(self):
        """Test WeeklySelectionData with secondary_movie_id defaulting to None."""
        selection = WeeklySelectionData(
            week_of="2024-01-15",
            master_of_ceremony="Jane",
            primary_movie_id="550",
        )
        assert selection.secondary_movie_id is None

    def test_weekly_selection_data_invalid_types(self):
        """Test that wrong types raise ValidationError."""
        with pytest.raises(ValidationError):
            WeeklySelectionData(
                week_of=123,  # Should be string
                master_of_ceremony="John",
                primary_movie_id="550",
            )

    def test_weekly_selection_data_missing_required(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            WeeklySelectionData(
                week_of="2024-01-15",
                # Missing master_of_ceremony and primary_movie_id
            )

    def test_weekly_selection_data_serialization(self):
        """Test JSON round-trip serialization."""
        selection = WeeklySelectionData(
            week_of="2024-01-15",
            master_of_ceremony="John",
            primary_movie_id="550",
            secondary_movie_id="551",
        )

        # Serialize to JSON
        json_data = selection.model_dump_json()

        # Deserialize back
        restored = WeeklySelectionData.model_validate_json(json_data)

        assert restored.week_of == selection.week_of
        assert restored.master_of_ceremony == selection.master_of_ceremony
        assert restored.primary_movie_id == selection.primary_movie_id
        assert restored.secondary_movie_id == selection.secondary_movie_id

    def test_weekly_selection_data_model_dump(self):
        """Test model_dump returns correct dictionary."""
        selection = WeeklySelectionData(
            week_of="2024-01-15",
            master_of_ceremony="John",
            primary_movie_id="550",
        )

        data = selection.model_dump()

        assert data == {
            "week_of": "2024-01-15",
            "master_of_ceremony": "John",
            "primary_movie_id": "550",
            "secondary_movie_id": None,
        }
