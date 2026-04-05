FROM python:3.12-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app


COPY reg.txt .

COPY config.py .

COPY main.py .

RUN pip install --no-cache-dir -r reg.txt
CMD ["python", "main.py"]
