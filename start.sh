#!/bin/sh
cd frontend
npm install
npm run build
cd ..
PYTHONUNBUFFERED=TRUE gunicorn -w 2 -k uvicorn.workers.UvicornWorker --config config.py main:app