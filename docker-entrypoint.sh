#!/bin/sh
set -e

# Apply pending database migrations before the server starts.
# Safe to run on every start: already applied migrations are skipped.
python manage.py migrate --noinput

exec "$@"
