#!/bin/sh
cd generation
pip install -r requirements.txt
python -m spacy download en_core_web_lg

cd ../frontend
npm install