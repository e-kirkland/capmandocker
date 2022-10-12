#!/bin/bash

if [ "$FLASK_ENV" = "production" ]
then
    echo "Starting Flask server in PRODUCTION mode..."
    # python manage.py create_db
    exec gunicorn --config /app/gunicorn_config.py project.wsgi:app
fi

if [ "$FLASK_ENV" = "local" ]
then
    echo "Starting Flask server in LOCAL mode"
    # python manage.py create_db
    python ./project/app.py
fi