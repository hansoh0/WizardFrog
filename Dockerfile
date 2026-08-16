# syntax=docker/dockerfile:1

FROM python:3.10-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*
    
RUN mkdir -p /home/wizardfrog/app

WORKDIR /app/py_components

COPY py_components/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY py_components/ .

ENV PYTHONUNBUFFERED=1

CMD ["python3", "main.py"]
