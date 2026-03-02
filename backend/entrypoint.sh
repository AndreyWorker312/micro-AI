#!/usr/bin/env sh
set -eu

python manage.py migrate --noinput

python -c "from api.asr import _get_model; _get_model(); print('Whisper model is ready')"

exec gunicorn server.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 1 \
  --threads 2 \
  --access-logfile - \
  --error-logfile - \
  --timeout 300

