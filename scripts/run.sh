#!/bin/bash

set -a
source .env
set +a

echo "Running server on port $PORT"

cd src
# Run server
uvicorn app.main:app --host "$HOST" --port "$PORT" --reload

cd ..