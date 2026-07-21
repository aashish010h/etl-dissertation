# Use a lightweight standard Python image for ECS Fargate
FROM python:3.12-slim

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install SSL root certificates
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements and install dependencies
COPY docker/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt

# Copy the ETL application entrypoint
COPY src/app.py /app/app.py

# ECS/Fargate will run this container entrypoint directly
ENTRYPOINT ["python", "/app/app.py"]