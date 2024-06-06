#!/bin/bash
source venv/bin/activate
flask db init
flask db migrate
flask db upgrade
chmod 666 /var/run/docker.sock
exec gunicorn -b :80 run:app