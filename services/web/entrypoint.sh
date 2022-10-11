#!/bin/sh

if [ "$FLASK_ENV" = "development" ]
then
    echo "Creating the database tables..."
    python manage.py create_db
    echo "Tables created"
fi

if [ "$FLASK_ENV" = "fly.io" ]
then
  echo "Launching docker image in fly.io"
  python manage.py run -h 0.0.0.0
  echo "Running app"
fi

python manage.py run -h 0.0.0.0 -p 8080
# gunicorn --bind 0.0.0.0:8080 manage:cli

exec "$@"