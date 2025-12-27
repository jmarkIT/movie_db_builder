# CLAUDE.md - AI Assistant Guide for movie_db_builder

## Project Overview

**movie_db_builder** is a Python CLI application that builds and populates a local SQLite database with movie data by integrating with multiple external APIs:

- **TMDB (The Movie Database)**: Fetches movie details, credits, and genres
- **Notion**: Retrieves weekly movie selections and movie lists from Notion databases
- **MusicBrainz**: Music release information (integration in progress)

The application is designed to sync movie data from Notion workspaces into a local database for analysis and tracking.

### Key Technologies

- **Python 3.14+** (cutting edge version requirement)
- **Typer**: CLI framework
- **Pydantic**: Data validation and serialization
- **SQLAlchemy**: ORM and database operations
- **httpx**: Modern HTTP client
- **python-dotenv**: Environment variable management
- **uv**: Package manager (note: uv.lock present)

## Project Structure

```
movie_db_builder/
├── src/movie_db_builder/
│   ├── __main__.py              # CLI entry point with main workflow
│   ├── models.py                # Shared Pydantic models
│   ├── utils.py                 # Helper functions for data transformation
│   │
│   ├── client/                  # HTTP client infrastructure
│   │   └── client.py            # Chain of Responsibility pattern implementation
│   │
│   ├── db/                      # Database layer
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   └── db.py                # Database operations and CRUD functions
│   │
│   ├── tmdb/                    # TMDB API integration
│   │   ├── tmdb_client.py       # TMDB API client
│   │   ├── tmdb_config.py       # Configuration for TMDB
│   │   └── models.py            # Pydantic models for TMDB responses
│   │
│   ├── notion/                  # Notion API integration
│   │   ├── notion_client.py     # Notion API client
│   │   ├── notion_config.py     # Configuration for Notion
│   │   └── models.py            # Pydantic models for Notion responses
│   │
│   └── music_brainz/            # MusicBrainz API integration
│       ├── music_brainz_client.py
│       ├── music_brainz_config.py
│       └── models.py
│
├── pyproject.toml               # Project configuration and dependencies
├── uv.lock                      # uv package manager lock file
├── .python-version              # Python version specification (3.14)
├── .gitignore                   # Ignores: __pycache__, .venv, .env, *.db
└── tmdb.csv                     # Data file (usage unclear)
```

## Architecture & Design Patterns

### 1. Modular API Client Design

Each external API has its own module with consistent structure:
- `*_client.py`: API client implementation
- `*_config.py`: Configuration dataclass/model
- `models.py`: Pydantic models for API responses

### 2. Chain of Responsibility Pattern (client/client.py)

The HTTP client uses a chain of responsibility pattern with composable handlers:

```python
HTTPExecutor          # Base executor using httpx
↓
RateLimiter          # Rate limiting with configurable requests/second
↓
RetryHandler         # Automatic retry with exponential backoff
↓
AuthProvider         # Adds authentication headers
↓
HTTPClient           # Final client with convenience methods
```

**Key Classes:**
- `HTTPExecutor`: Performs actual HTTP requests
- `RateLimiter`: Enforces rate limits between requests
- `RetryHandler`: Retries on 429, 500, 502, 503, 504 status codes
- `AuthProvider`: Injects authentication headers
- `HTTPClient`: High-level client with base URL handling

**Note**: Currently, individual API clients (TMDB, Notion) don't use this infrastructure yet. Consider migrating them to use the composable HTTP client.

### 3. Database Layer Architecture

Uses SQLAlchemy 2.0+ with:
- **Declarative Base** pattern
- **Mapped columns** with type annotations
- **Upsert operations** via SQLite's `INSERT ... ON CONFLICT`
- **Many-to-many relationships** for movies↔genres and movies↔people

**Database Models:**
- `Movie`: Core movie data (id, title, budget, revenue, runtime)
- `Genre`: Movie genres
- `Person`: Cast and crew members
- `MovieToGenre`: Junction table for movie-genre relationships
- `MovieToPerson`: Junction table with role details (cast/crew)
- `WeeklySelection`: Weekly movie picks with master of ceremony

### 4. Data Flow

```
Notion API → NotionClient → NotionPage models
                ↓
         extract_movie_pages()
                ↓
         build_weekly_selections()
                ↓
            WeeklySelectionData

TMDB API → TMDBClient → TMDBMovie models
              ↓
         Database functions (add_tmdb_movies, etc.)
              ↓
          SQLite database
```

## Code Conventions & Patterns

### Python Style

1. **Type Hints**: Comprehensive type annotations throughout
   - Use `|` for unions (e.g., `str | None`)
   - Use `list[Type]` and `dict[str, Type]` (modern Python 3.10+ syntax)

2. **Pydantic Models**:
   - Used for all API response parsing
   - Optional fields use `| None = None`
   - Custom properties for computed values (e.g., `plain_text` in NotionProperty)

3. **Error Handling**:
   - Raise `TypeError` for parsing failures with context
   - Raise `RuntimeError` for API/network issues
   - Include original data in error messages for debugging

4. **Async/Sync**:
   - Main workflow uses `asyncio.run(async_main())`
   - MusicBrainz client uses async context manager
   - TMDB and Notion clients are synchronous

### Database Operations

1. **Upsert Pattern**:
   ```python
   stmt = insert(Model).values([...])
   stmt = stmt.on_conflict_do_update(...)  # or on_conflict_do_nothing()
   ```

2. **Session Management**:
   - Use context managers: `with Session(engine) as session:`
   - Always commit after execute

3. **Bulk Operations**:
   - Use list comprehensions to prepare batch values
   - Single insert with multiple values for efficiency

### API Client Patterns

1. **Retry Logic** (Notion):
   - 3 retries with exponential backoff (0.5 * 2^attempt)
   - Retry on: 429, 500, 502, 503, 504, timeouts, request errors
   - Raise detailed RuntimeError on final failure

2. **Request Method**:
   ```python
   def perform_request(
       self,
       endpoint: str,
       method: str = "GET",
       params: dict | None = None,
       data: dict | None = None,
   ) -> httpx.Response | None
   ```

3. **Pagination** (Notion):
   - Follow `has_more` flag
   - Use `next_cursor` for subsequent requests

### Environment Variables

Required environment variables (checked in `__main__.py:35-50`):
- `TMDB_TOKEN`: TMDB API bearer token
- `NOTION_TOKEN`: Notion API key
- `MOVIE_DATASOURCE_ID`: Notion database ID for movies
- `WEEK_DATASOURCE_ID`: Notion database ID for weekly selections

**Loading**: Use `python-dotenv` to load from `.env` file (not committed to git)

## Development Workflow

### Setup

1. **Python Version**: Ensure Python 3.14 is installed
   ```bash
   python --version  # Should be 3.14.x
   ```

2. **Install Dependencies**:
   ```bash
   uv sync  # or pip install -e .
   ```

3. **Environment Setup**:
   Create `.env` file in project root:
   ```env
   TMDB_TOKEN=your_token_here
   NOTION_TOKEN=your_token_here
   MOVIE_DATASOURCE_ID=your_database_id
   WEEK_DATASOURCE_ID=your_database_id
   ```

### Running the Application

```bash
db_builder  # Main entry point defined in pyproject.toml
```

Or directly:
```bash
python -m movie_db_builder
```

### Database

- **Location**: `movies.db` in project root (gitignored)
- **Schema**: Auto-created via `create_db(engine)` on each run
- **Persistence**: Uses upsert operations, safe to run multiple times

## File-by-File Guide

### Core Entry Point

**`__main__.py:31-126`** - Main workflow:
1. Create SQLite database
2. Validate environment variables
3. Initialize API clients (TMDB, Notion, MusicBrainz)
4. Fetch weekly selections from Notion
5. Fetch movie list from Notion
6. Get movie details from TMDB
7. Populate database with movies, genres, credits, and selections

### Database Layer

**`db/models.py`** - SQLAlchemy ORM models:
- Clear separation between ORM models and Pydantic models
- Junction tables for many-to-many relationships
- Foreign key constraints properly defined

**`db/db.py`** - Database operations:
- `create_db()`: Initialize schema
- `add_tmdb_movies()`: Upsert movies with conflict resolution
- `add_tmdb_genres()`: Insert genres (ignore conflicts)
- `add_tmdb_movie_to_genre()`: Create movie-genre relationships
- `add_tmdb_credits()`: Insert cast and crew
- `add_tmdb_movie_to_person()`: Create movie-person relationships
- `add_weekly_selection()`: Insert weekly picks

### API Clients

**`tmdb/tmdb_client.py`**:
- `get_movie_details(movie_id, append_to_response)`: Fetch movie with optional expansions
- `get_genres()`: Fetch all available genres
- Note: No retry/rate limiting yet (consider using client/client.py infrastructure)

**`notion/notion_client.py`**:
- `get_page(page_id)`: Fetch single Notion page
- `get_datasource_rows(data_source_id)`: Query database with automatic pagination
- Built-in retry logic with exponential backoff
- 10-second timeout with 5-second connect timeout

**`music_brainz/music_brainz_client.py`**:
- Async implementation with context manager
- Currently just a test call in main (line 62-66)

### Utilities

**`utils.py`**:
- `extract_movie_pages()`: Extract movie pages from weekly selection relations
- `build_weekly_selections()`: Transform Notion pages to WeeklySelectionData
- Note: Uses `.count` property which may not exist on lists (potential bug)

## Common Tasks for AI Assistants

### Adding a New API Integration

1. Create module: `src/movie_db_builder/new_api/`
2. Add files:
   - `new_api_config.py`: Config dataclass with API credentials
   - `models.py`: Pydantic models for API responses
   - `new_api_client.py`: Client class
   - `__init__.py`: Public exports
3. Consider using `client/client.py` infrastructure for HTTP handling
4. Add to `__main__.py` workflow if needed

### Adding Database Models

1. Add ORM model to `db/models.py`
2. Add CRUD function to `db/db.py`
3. Create corresponding Pydantic model in `models.py` or API-specific models
4. Update `__main__.py` to populate new data

### Modifying the Workflow

Main workflow is in `__main__.py:async_main()`. It's currently linear and runs all operations. To modify:
- Add CLI arguments via Typer decorators
- Break into smaller functions for testability
- Add error handling and rollback logic

### Testing

**Note**: No test suite currently exists. When adding tests:
- Use pytest
- Mock external API calls
- Test database operations with in-memory SQLite
- Test Pydantic model validation

## Known Issues & Improvement Opportunities

### Potential Bugs

1. **`utils.py:30`**: Uses `movies.count` which doesn't exist on `list`
   - Should be `len(movies)`
   - Also at line 17: `relations.count`

2. **Notion indentation issue** (`notion_client.py:139-140`):
   - `close()` method is indented inside `get_datasource_rows()`
   - Should be at class level

3. **TMDB Error Handling**:
   - `perform_request()` can return `None` but match statement doesn't handle it
   - Should raise exception for unsupported methods

### Architectural Improvements

1. **Migrate API Clients to Chain of Responsibility Pattern**:
   - TMDB and Notion clients could benefit from the `client/client.py` infrastructure
   - Would add rate limiting and consistent retry logic

2. **Configuration Management**:
   - Use Pydantic Settings for environment variables
   - Validate on startup rather than runtime checks

3. **Async Consistency**:
   - MusicBrainz is async, others are sync
   - Consider making all API clients async for consistency

4. **Error Recovery**:
   - No rollback on partial failures
   - Database could be in inconsistent state if API calls fail mid-run

5. **Logging**:
   - Currently uses print statements
   - Add proper logging with levels and structured output

6. **Testing**:
   - No test coverage
   - Add unit tests for models, integration tests for API clients

## Dependencies Deep Dive

From `pyproject.toml`:

- **httpx>=0.28.1**: Modern async-capable HTTP client (successor to requests)
- **pydantic>=2.12.4**: Data validation using Python type annotations (v2 API)
- **python-dotenv>=1.2.1**: Load environment variables from .env
- **sqlalchemy>=2.0.44**: ORM using modern 2.0 style with type annotations
- **typer>=0.20.0**: CLI framework built on Click

**Python Version**: Requires >=3.14 (note: 3.14 is not yet released as of early 2024, may need adjustment)

## Git Workflow

Current branch: `claude/add-claude-documentation-eSsRQ`

### Commit Guidelines

- Use descriptive commit messages
- Reference issue numbers if applicable
- Recent commits show iterative development style

### Ignored Files (.gitignore)

- `__pycache__/`, `*.py[oc]`: Python bytecode
- `build/`, `dist/`, `*.egg-info`: Build artifacts
- `.venv`: Virtual environment
- `.env`: Environment variables (secrets)
- `*.db`: SQLite databases

## Quick Reference

### Entry Point
```bash
db_builder  # Defined in pyproject.toml [project.scripts]
```

### Adding New Dependencies
```bash
uv add package-name  # or pip install and update pyproject.toml
```

### Database Location
```
./movies.db  # Created in project root
```

### Key Files to Modify for Common Changes

- **Add CLI command**: `__main__.py` (add Typer command)
- **Change workflow**: `__main__.py:async_main()`
- **Add database table**: `db/models.py` + `db/db.py`
- **Modify API call**: `{api}/client.py` and `{api}/models.py`
- **Add utility function**: `utils.py`
- **Configure new env var**: `.env` + validation in `__main__.py`

## Best Practices for AI Assistants

1. **Read Before Modifying**: Always read existing files before suggesting changes
2. **Follow Existing Patterns**: Match the coding style and architecture already in use
3. **Type Everything**: Maintain comprehensive type hints
4. **Validate Early**: Add Pydantic models for all external data
5. **Handle Errors**: Include detailed error messages with context
6. **Use Upserts**: Database operations should be idempotent when possible
7. **Check Environment**: Validate required environment variables early
8. **Document Changes**: Update this file when making architectural changes
9. **Test Compatibility**: Remember Python 3.14 requirement
10. **Mind the Database**: Operations are not transactional across API calls

## Resources

- [TMDB API Docs](https://developer.themoviedb.org/docs)
- [Notion API Docs](https://developers.notion.com/)
- [MusicBrainz API Docs](https://musicbrainz.org/doc/MusicBrainz_API)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/en/20/)
- [Pydantic V2 Docs](https://docs.pydantic.dev/latest/)
- [Typer Docs](https://typer.tiangolo.com/)

---

**Last Updated**: 2025-12-27
**Document Version**: 1.0.0
**Project Version**: 0.1.0
