#!/bin/bash
apt-get update && apt-get install -y poppler-utils tesseract-ocr
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8080
