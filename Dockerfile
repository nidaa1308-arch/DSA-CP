FROM python:3.11-slim

WORKDIR /app

# Install system libraries for geospatial support
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgeos-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/backend/
COPY run.py /app/run.py

ENV PYTHONPATH=/app/backend
ENV PORT=8000

EXPOSE 8000

CMD ["python", "run.py"]
