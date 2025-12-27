"""Shared fixtures for all tests.

NOTE: Due to forward reference issues in the source code (classes reference
other classes before they're defined), we keep imports minimal here.
Individual test files will handle their own imports.

Known forward reference issues:
- src/movie_db_builder/tmdb/models.py: TMDBMovie references TMDBGenre before definition
- src/movie_db_builder/notion/models.py: NotionPage references NotionProperty before definition
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

import sys
sys.path.insert(0, "/home/user/movie_db_builder/src")


@pytest.fixture
def in_memory_engine() -> Engine:
    """Create an in-memory SQLite engine for testing."""
    from movie_db_builder.db.db import create_db
    from movie_db_builder.db.models import Base

    engine = create_engine("sqlite:///:memory:")
    create_db(engine)
    return engine
