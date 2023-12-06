#!/bin/bash
# wait until postgres run
./wait-for-it.sh db:5432

# migrate database
alembic upgrade head

# then run the app
exec hypercorn -b 0.0.0.0:8000 --workers 4 --access-logfile - --error-logfile - asgi:app
