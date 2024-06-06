#!/bin/bash
source venv/bin/activate
exec gunicorn -b :80 run:app