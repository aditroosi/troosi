# Use Python 3.12.4 base image
FROM python:3.12.4-slim
# Install required system dependencies for opencv-python
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    ffmpeg \
    libgl1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# Set working directory
WORKDIR /app

# Copy requirements and source code
COPY requirements.txt .
COPY . .

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Default command
CMD ["python", "all_process.py"]
