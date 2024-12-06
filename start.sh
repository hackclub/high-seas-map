#!/bin/sh
python -m spacy download en_core_web_sm
PYTHONUNBUFFERED=1 gunicorn -w 2 -k uvicorn.workers.UvicornWorker --config config.py -t 600 main:app