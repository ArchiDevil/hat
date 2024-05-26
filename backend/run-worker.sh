#!/bin/bash
# wait until postgres run
./wait-for-it.sh db:5432

# then run the worker
python3 worker.py
