FROM python:3.12-slim

# Dependencias del sistema para pdfplumber y python-magic
RUN apt-get update && apt-get install -y \
    libmagic1 \
    poppler-utils \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
