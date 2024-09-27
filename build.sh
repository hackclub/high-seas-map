#!/bin/sh
cd generation
python3 main.py all
cd ../frontend
npx vite build