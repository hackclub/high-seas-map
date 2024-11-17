#!/bin/sh
cd frontend
npm install
npm run build
cd ..
python -m spacy download en_core_web_md
gunicorn -w 2 -k uvicorn.workers.UvicornWorker --config config.py main:app