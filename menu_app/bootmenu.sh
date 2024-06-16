#!/bin/bash
source venv/bin/activate
until pg_isready -h resos_menu_postgres -p 5432; do
    echo "$(date) - Ожидание подключения к базе данных..."
    sleep 1
done
exec gunicorn -b :80 run:app