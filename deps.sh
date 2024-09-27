#!/bin/sh

dnf install -y python3 python3-pip

cd generation
pip install -r requirements.txt
python -m spacy download en_core_web_lg

cd ../frontend
npm install