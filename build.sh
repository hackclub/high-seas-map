#!/bin/sh
cd generation
source .venv/bin/activate
python3 main.py all
cd ../frontend
npx vite build