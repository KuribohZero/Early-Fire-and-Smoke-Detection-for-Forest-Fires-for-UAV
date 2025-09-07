FROM python:3.12-slim

WORKDIR /code

# Install system dependencies for OpenCV, Picamera2, and missing GLib libraries
RUN apt-get update && apt-get install -y \
    libgl1 \
    libsm6 \
    libxext6 \
    libjpeg-dev \
    gcc \
    g++ \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY ./requirements.txt /code/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy project files
COPY ./ /code

# Run FastAPI
CMD ["uvicorn", "fireDetectionApp.main:app", "--host", "0.0.0.0", "--port", "8000"]
