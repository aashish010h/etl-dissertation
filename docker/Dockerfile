# Use a lightweight standard Python image for Fargate
FROM python:3.12-slim

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy the Fargate requirements and install them
COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the unified ETL script
COPY src/app.py .

# Fargate runs the script directly
CMD ["python", "app.py"]