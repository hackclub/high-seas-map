#!/bin/sh
cd generation
python main.py all
cd ../frontend
vite build