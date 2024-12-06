#!/bin/sh
PYTHONUNBUFFERED=1 gunicorn -w 2 -k uvicorn.workers.UvicornWorker --config config.py -t 600 main:app