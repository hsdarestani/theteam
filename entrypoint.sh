#!/bin/sh
set -e
python manage.py migrate --noinput
python manage.py localize_demo_data
python manage.py collectstatic --noinput
exec "$@"
