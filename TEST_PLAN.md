# Test Plan: movie_db_builder

## Overview

This document outlines the test strategy for the `movie_db_builder` project. The project currently has no test coverage. This plan follows the recommendations in CLAUDE.md:

- Use pytest
- Mock external API calls
- Test database operations with in-memory SQLite
- Test Pydantic model validation

## Test Framework & Dependencies

Add to `pyproject.toml`:

```toml
[project.optional-dependencies]
test = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.14.0",
    "respx>=0.21.0",  # httpx mocking
]
```

## Directory Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_models.py           # Pydantic model tests
├── test_db/
│   ├── conftest.py          # Database fixtures
│   ├── test_orm_models.py   # SQLAlchemy model tests
│   └── test_db_operations.py # CRUD function tests
├── test_client/
│   └── test_http_client.py  # Chain of Responsibility tests
├── test_tmdb/
│   ├── test_models.py       # TMDB Pydantic models
│   └── test_client.py       # TMDBClient tests
├── test_notion/
│   ├── test_models.py       # Notion Pydantic models
│   └── test_client.py       # NotionClient tests
├── test_music_brainz/
│   └── test_client.py       # MusicBrainzClient tests
├── test_utils.py            # Utility function tests
└── test_main.py             # Workflow integration tests
```

---

## 1. Pydantic Model Tests

### 1.1 Core Models (`test_models.py`)

**Target:** `src/movie_db_builder/models.py`

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_weekly_selection_data_valid` | All required fields provided | High |
| `test_weekly_selection_data_optional_secondary` | secondary_movie_id as None | High |
| `test_weekly_selection_data_invalid_types` | Wrong types raise ValidationError | Medium |
| `test_weekly_selection_data_serialization` | JSON round-trip works | Medium |

### 1.2 TMDB Models (`test_tmdb/test_models.py`)

**Target:** `src/movie_db_builder/tmdb/models.py`

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_tmdb_movie_valid` | Full movie with genres and credits | High |
| `test_tmdb_movie_no_credits` | Movie with credits=None | High |
| `test_tmdb_movie_empty_genres` | Movie with empty genres list | Medium |
| `test_tmdb_genre_valid` | Genre instantiation | High |
| `test_tmdb_genres_query_wrapper` | TMDBGenresQuery wraps list | Medium |
| `test_tmdb_person_cast_member` | Person with cast fields | High |
| `test_tmdb_person_crew_member` | Person with crew fields | High |
| `test_tmdb_credits_valid` | Credits with cast and crew | Medium |

### 1.3 Notion Models (`test_notion/test_models.py`)

**Target:** `src/movie_db_builder/notion/models.py`

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_notion_page_valid` | Full page instantiation | High |
| `test_notion_property_plain_text_from_title` | Extract text from title type | High |
| `test_notion_property_plain_text_from_rich_text` | Extract text from rich_text | High |
| `test_notion_property_plain_text_concatenation` | Multiple rich_text items | Medium |
| `test_notion_property_plain_text_none_for_other_types` | Non-text types return None | Medium |
| `test_notion_database_query_response_pagination` | has_more and next_cursor | High |
| `test_notion_relation_id_extraction` | Relation ID parsing | Medium |
| `test_notion_date_with_end` | Date with start and end | Medium |
| `test_notion_select_property` | Select with name and color | Medium |

### 1.4 MusicBrainz Models (`test_music_brainz/test_models.py`)

**Target:** `src/movie_db_builder/music_brainz/models.py`

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_musicbrainz_release_valid` | Release with genres | Low |
| `test_musicbrainz_genre_valid` | Genre instantiation | Low |

---

## 2. Database Tests

### 2.1 Fixtures (`test_db/conftest.py`)

```python
import pytest
from sqlalchemy import create_engine
from movie_db_builder.db.models import Base
from movie_db_builder.db.db import create_db

@pytest.fixture
def in_memory_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    create_db(engine)
    return engine

@pytest.fixture
def sample_tmdb_movie():
    """Sample TMDBMovie for testing."""
    from movie_db_builder.tmdb.models import TMDBMovie, TMDBGenre
    return TMDBMovie(
        id=550,
        title="Fight Club",
        budget=63000000,
        revenue=100853753,
        runtime=139,
        genres=[TMDBGenre(id=18, name="Drama")],
        credits=None
    )
```

### 2.2 ORM Model Tests (`test_db/test_orm_models.py`)

**Target:** `src/movie_db_builder/db/models.py`

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_movie_creation` | Movie ORM object instantiation | High |
| `test_movie_repr` | __repr__ format (fix bug: missing `=`) | Medium |
| `test_genre_creation` | Genre ORM object | Medium |
| `test_person_with_optional_fields` | Person with NULL known_for_department | Medium |
| `test_movie_to_genre_composite_key` | Junction table PK | Medium |
| `test_movie_to_person_credit_id_pk` | Credit ID as primary key | Medium |
| `test_weekly_selection_fk_constraints` | Foreign keys to Movie | High |

### 2.3 Database Operation Tests (`test_db/test_db_operations.py`)

**Target:** `src/movie_db_builder/db/db.py`

| Test Case | Description | Priority |
|-----------|-------------|----------|
| **create_db** | | |
| `test_create_db_creates_all_tables` | All 6 tables created | High |
| `test_create_db_idempotent` | Can run multiple times | High |
| **add_tmdb_movies** | | |
| `test_add_single_movie` | Insert one movie | High |
| `test_add_multiple_movies` | Insert multiple movies | High |
| `test_add_movies_empty_list` | Empty list no-op | Medium |
| `test_add_movies_upsert_updates` | Existing ID updates budget/revenue/runtime | High |
| `test_add_movies_large_integers` | Large budget/revenue values | Medium |
| **add_tmdb_genres** | | |
| `test_add_single_genre` | Insert one genre | High |
| `test_add_genres_duplicate_ignored` | Conflict does nothing | High |
| `test_add_genres_empty_list` | Empty list no-op | Medium |
| **add_tmdb_movie_to_genre** | | |
| `test_add_movie_genre_relationship` | Link movie to genre | High |
| `test_add_movie_multiple_genres` | Movie with multiple genres | High |
| `test_add_movie_no_genres` | Movie with empty genres | Medium |
| **add_tmdb_credits** | | |
| `test_add_cast_members` | Insert cast as Person | High |
| `test_add_crew_members` | Insert crew as Person | High |
| `test_add_credits_duplicate_person` | Same person in multiple movies | Medium |
| `test_add_credits_null_credits` | Movie.credits is None | Medium |
| **add_tmdb_movie_to_person** | | |
| `test_add_cast_relationship` | Cast with character/order | High |
| `test_add_crew_relationship` | Crew with department/job | High |
| `test_add_duplicate_credit_id` | Conflict handling | Medium |
| **add_weekly_selection** | | |
| `test_add_single_selection` | Insert one selection | High |
| `test_add_selection_with_secondary` | With secondary_movie_id | High |
| `test_add_selection_without_secondary` | secondary_movie_id is None | High |
| `test_add_selection_duplicate_week` | Conflict does nothing | Medium |

---

## 3. HTTP Client Tests (Chain of Responsibility)

**Target:** `src/movie_db_builder/client/client.py`

### 3.1 Handler Tests (`test_client/test_http_client.py`)

| Test Case | Description | Priority |
|-----------|-------------|----------|
| **HTTPExecutor** | | |
| `test_executor_get_request` | Executes GET with correct params | High |
| `test_executor_post_request` | Executes POST with JSON body | High |
| `test_executor_raises_on_error` | Raises HTTPStatusError for 4xx/5xx | High |
| **RateLimiter** | | |
| `test_rate_limiter_first_request_no_delay` | First request immediate | High |
| `test_rate_limiter_enforces_delay` | Subsequent requests wait | High |
| `test_rate_limiter_custom_rate` | Different requests_per_second | Medium |
| **RetryHandler** | | |
| `test_retry_success_first_attempt` | No retry on success | High |
| `test_retry_on_429` | Retries rate limit errors | High |
| `test_retry_on_5xx` | Retries server errors | High |
| `test_no_retry_on_4xx` | No retry for client errors | High |
| `test_retry_max_attempts_exceeded` | Raises after max retries | High |
| `test_retry_exponential_backoff` | Backoff timing verification | Medium |
| **AuthProvider** | | |
| `test_auth_provider_injects_headers` | Adds auth headers | High |
| `test_auth_provider_merges_headers` | Combines with existing | Medium |
| **HTTPClient** | | |
| `test_http_client_url_construction` | base_url + endpoint | High |
| `test_http_client_get_convenience` | get() method | Medium |
| `test_http_client_post_convenience` | post() method | Medium |
| `test_http_client_default_headers` | Content-Type added | Medium |

---

## 4. API Client Tests

### 4.1 TMDB Client (`test_tmdb/test_client.py`)

**Target:** `src/movie_db_builder/tmdb/tmdb_client.py`

Use `respx` to mock httpx requests.

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_get_movie_details_success` | Valid response parsed | High |
| `test_get_movie_details_with_credits` | append_to_response=credits | High |
| `test_get_movie_details_not_found` | 404 handling | High |
| `test_get_movie_details_parse_error` | Invalid JSON raises TypeError | Medium |
| `test_get_genres_success` | Returns genre list | High |
| `test_get_genres_empty` | Empty genres list | Medium |
| `test_perform_request_auth_header` | Bearer token in Authorization | High |
| `test_perform_request_unsupported_method` | PUT/DELETE return None | Medium |

### 4.2 Notion Client (`test_notion/test_client.py`)

**Target:** `src/movie_db_builder/notion/notion_client.py`

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_get_page_success` | Valid page parsed | High |
| `test_get_page_not_found` | RuntimeError on None response | High |
| `test_get_datasource_rows_single_page` | No pagination | High |
| `test_get_datasource_rows_pagination` | Multiple pages fetched | High |
| `test_get_datasource_rows_empty` | Empty results | Medium |
| `test_perform_request_retry_on_429` | Rate limit retry | High |
| `test_perform_request_retry_on_5xx` | Server error retry | High |
| `test_perform_request_backoff_timing` | Exponential backoff | Medium |
| `test_perform_request_max_retries` | RuntimeError after exhaustion | High |
| `test_perform_request_headers` | Notion-Version header | Medium |

### 4.3 MusicBrainz Client (`test_music_brainz/test_client.py`)

**Target:** `src/movie_db_builder/music_brainz/music_brainz_client.py`

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_client_initialization` | Handler chain setup | Low |
| `test_user_agent_format` | Correct User-Agent header | Low |
| `test_http_client_accessible` | self.http available | Low |

---

## 5. Utility Function Tests

**Target:** `src/movie_db_builder/utils.py`

### 5.1 Tests (`test_utils.py`)

| Test Case | Description | Priority |
|-----------|-------------|----------|
| **extract_movie_pages** | | |
| `test_extract_single_movie` | One movie relation | High |
| `test_extract_two_movies` | Two movie relations | High |
| `test_extract_missing_movie_property` | Raises TypeError | High |
| `test_extract_calls_client_get_page` | Mocked client verification | Medium |
| **build_weekly_selections** | | |
| `test_build_single_movie_selection` | One movie | High |
| `test_build_two_movie_selection` | Two movies | High |
| `test_build_extracts_week_of` | Date extraction | High |
| `test_build_extracts_master_of_ceremony` | Select property | High |
| `test_build_extracts_tmdb_ids` | Number to string cast | Medium |

**Note:** Tests should expose the bugs at lines 17 and 30 where `relations.count` and `movies.count` should be `len(relations)` and `len(movies)`.

---

## 6. Integration Tests

**Target:** `src/movie_db_builder/__main__.py`

### 6.1 Workflow Tests (`test_main.py`)

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_missing_tmdb_token_exits` | typer.Exit(1) on missing env | High |
| `test_missing_notion_token_exits` | typer.Exit(1) on missing env | High |
| `test_missing_movie_datasource_exits` | typer.Exit(1) on missing env | High |
| `test_missing_week_datasource_exits` | typer.Exit(1) on missing env | High |
| `test_full_workflow_success` | End-to-end with mocked APIs | Medium |
| `test_database_population_order` | Correct sequence of db calls | Medium |

---

## 7. Known Bugs to Capture in Tests

These tests should initially fail, proving the bugs exist:

| Location | Bug | Test to Write |
|----------|-----|---------------|
| `utils.py:17` | `relations.count` should be `len(relations)` | `test_extract_movie_pages_uses_len` |
| `utils.py:30` | `movies.count` should be `len(movies)` | `test_build_weekly_selections_uses_len` |
| `db/models.py:19` | `__repr__` has `title{` instead of `title={` | `test_movie_repr_format` |
| `db/models.py:29` | `__repr__` has `name{` instead of `name={` | `test_genre_repr_format` |
| `notion_client.py:139` | `close()` indented inside `get_datasource_rows()` | `test_close_is_class_method` |

---

## 8. Test Configuration

### pytest.ini / pyproject.toml

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --cov=src/movie_db_builder --cov-report=term-missing"
filterwarnings = [
    "ignore::DeprecationWarning",
]
```

### Coverage Target

| Component | Target | Notes |
|-----------|--------|-------|
| Pydantic Models | 95% | Validation is critical |
| Database Layer | 90% | Core functionality |
| API Clients | 85% | External dependencies mocked |
| Utilities | 95% | Pure functions |
| HTTP Client | 80% | Handler chain |
| Main Workflow | 70% | Integration complexity |

---

## 9. Execution Plan

### Phase 1: Foundation (High Priority)
1. Set up pytest infrastructure and fixtures
2. Test all Pydantic models
3. Test database CRUD operations

### Phase 2: API Clients (High Priority)
4. Test TMDB client with mocked responses
5. Test Notion client with mocked responses

### Phase 3: Chain of Responsibility (Medium Priority)
6. Test HTTP client infrastructure
7. Test retry and rate limiting logic

### Phase 4: Utilities & Integration (Medium Priority)
8. Test utility functions
9. Add integration tests for main workflow

### Phase 5: Edge Cases & Bug Fixes (Low Priority)
10. Add tests that expose known bugs
11. Fix bugs and verify tests pass

---

## 10. Commands

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/movie_db_builder --cov-report=html

# Run specific test file
uv run pytest tests/test_db/test_db_operations.py

# Run tests matching pattern
uv run pytest -k "test_add_movie"

# Run only high priority (mark tests with @pytest.mark.priority)
uv run pytest -m "high_priority"
```

---

## Summary

| Category | Test Count | Priority |
|----------|------------|----------|
| Pydantic Models | 25+ | High |
| Database ORM | 8 | Medium |
| Database Operations | 22 | High |
| HTTP Client Chain | 18 | Medium |
| TMDB Client | 8 | High |
| Notion Client | 10 | High |
| MusicBrainz Client | 3 | Low |
| Utilities | 9 | High |
| Integration | 6 | Medium |
| **Total** | **109+** | |

This test plan provides comprehensive coverage for the `movie_db_builder` project, focusing on the critical paths first while building toward full test coverage.
