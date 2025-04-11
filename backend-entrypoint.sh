#!/bin/sh

# collectstatic files
python manage.py collectstatic --noinput

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

# Start server
echo "Starting server"
uvicorn iransanad.asgi:application --host 0.0.0.0 --port 8000