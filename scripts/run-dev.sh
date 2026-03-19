#!/bin/bash

set -a
source .env
set +a

echo "Running server on port $PORT"

# Run mypy
# MYPYPATH=./src mypy src/app/main.py
if [ $? -ne 0 ]; then
    echo "Mypy had some errors, please fix before proceeding..."
    exit $?
fi

# Run formatters and linters
black src/
pylint -j4 src/
cd src
# Run server
uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
