#!/bin/sh

dnf install -y python3 python3-pip cairo python3-cairo cairo-devel python3-devel

cd generation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m spacy download en_core_web_lg

cd ../frontend
npm install