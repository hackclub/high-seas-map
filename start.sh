#!/bin/sh
npm install
npm run build
PYTHONUNBUFFERED=TRUE gunicorn -w 2 -k uvicorn.workers.UvicornWorker --config config.py main:app