"""Database-specific test fixtures.

NOTE: The source code has forward reference issues that prevent direct imports.
- tmdb/models.py: TMDBMovie references TMDBGenre before it's defined
- notion/models.py: NotionPage references NotionProperty before it's defined
- db/db.py: imports from tmdb/models.py, so it inherits the issue

We use pytest.importorskip and lazy imports to work around this where possible.
Tests that cannot run due to these issues are marked appropriately.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

import sys
sys.path.insert(0, "/home/user/movie_db_builder/src")

from movie_db_builder.models import WeeklySelectionData


@pytest.fixture
def in_memory_engine() -> Engine:
    """Create an in-memory SQLite engine for testing.

    This fixture will fail if the source code forward reference issues
    are not fixed (TMDBMovie references TMDBGenre before definition).
    """
    # Import db.models directly - it doesn't have the forward reference issue
    from movie_db_builder.db.models import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def sample_weekly_selection() -> WeeklySelectionData:
    """Sample WeeklySelectionData for testing."""
    return WeeklySelectionData(
        week_of="2024-01-15",
        master_of_ceremony="John",
        primary_movie_id="550",
        secondary_movie_id=None,
    )


@pytest.fixture
def sample_weekly_selection_with_secondary() -> WeeklySelectionData:
    """Sample WeeklySelectionData with secondary movie for testing."""
    return WeeklySelectionData(
        week_of="2024-01-22",
        master_of_ceremony="Jane",
        primary_movie_id="550",
        secondary_movie_id="680",
    )
