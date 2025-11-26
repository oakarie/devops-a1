# Base image for GPT Findability Tracker (A2 deployment)
FROM python:3.11-slim

# Keep things tidy and predictable inside the container
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so Docker can cache the expensive step
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . /app

# FastAPI listens on 8000; keep it open for the grader
EXPOSE 8000

# Simple uvicorn command for the assignment deployment
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

