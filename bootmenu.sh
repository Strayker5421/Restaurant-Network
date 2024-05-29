#!/bin/bash
source venv/bin/activate
exec gunicorn -b :8082 run:app