#!/bin/bash
# migrate database
alembic upgrade head

# then run the app
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --ws none
