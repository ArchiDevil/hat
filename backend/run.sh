#!/bin/bash
# wait until postgres run
./wait-for-it.sh db:5432

# migrate database
alembic upgrade head

# then run the app
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --ws none
