#!/bin/bash
source venv/bin/activate

if [ -d "migrations" ] && [ "$(ls -A migrations)" ]; then
    echo "Migrations directory exists and is not empty. Running upgrade..."
else
    echo "Migrations directory does not exist or is empty. Initializing and migrating..."
    flask db init
fi

until flask db migrate && flask db upgrade; do
    echo "Upgrade command failed, retrying in 5 secs..."
    sleep 5
done

chmod 666 /var/run/docker.sock
exec gunicorn -b :80 run:app