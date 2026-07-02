FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Production (Render / Docker): gunicorn via run:app
# Local dev alternative: CMD ["python", "run.py"]
CMD ["gunicorn", "--timeout", "120", "app:app"]
