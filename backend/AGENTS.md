# Project Instructions

## Running Tests

This project uses **pytest** with `asyncio_mode = "auto"`.

**Always** invoke pytest via the venv Python directly. Do **not** run `pytest` or `python` from the global environment, and do **not** use `.venv\Scripts\activate` — it does not work reliably on Windows in this context.

Run all tests:

```
.venv\Scripts\python.exe -m pytest
```

Run a specific test file:

```
.venv\Scripts\python.exe -m pytest tests/test_security.py
```

Run a specific test by name:

```
.venv\Scripts\python.exe -m pytest tests/test_security.py -k "test_name"
```

Run with verbose output:

```
.venv\Scripts\python.exe -m pytest -v
```

Run a specific test by name:

```
.venv\Scripts\python.exe -m pytest tests/test_security.py -k "test_name"
```

Run with coverage:

```
.venv\Scripts\python.exe -m pytest --cov
```

## Database Migrations

This project uses **Alembic** for database migrations.

**Always** create migrations using Alembic's `revision` command. Do **not** manually create migration files.

```
.venv\Scripts\python.exe -m alembic revision -m "descriptive_message_here"
```

Migration filenames follow the pattern `<revision_id>_<snake_case_description>.py` (e.g. `32d5a77e6615_add_comment_table.py`). Alembic generates the revision ID automatically.

Every migration must include both `upgrade()` and `downgrade()` functions that support **online mode** (connected to the database via `op` operations) and **offline mode** (raw SQL generation via `op.execute()` with proper SQL strings). Use Alembic's `op` API for online mode and provide equivalent SQL for offline mode using `context.is_offline_mode()`:

```python
from alembic import context

def upgrade() -> None:
    if context.is_offline_mode():
        op.execute("ALTER TABLE ...")
    else:
        op.alter_column(...)
```
