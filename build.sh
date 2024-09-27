#!/bin/sh
cd generation
python main.py all
cd ../frontend
npx vite build