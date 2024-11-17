#!/bin/sh
python -m spacy download en_core_web_md
gunicorn -w 2 -k uvicorn.workers.UvicornWorker --config config.py main:app