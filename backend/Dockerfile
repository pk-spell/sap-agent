FROM python:3.11-slim

# Installiere curl für Healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kopiere und installiere Requirements ZUERST (für besseren Cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# DANN kopiere den Rest
COPY . .

EXPOSE 8000

# V3 Backend
CMD ["python", "main_v3.py"]