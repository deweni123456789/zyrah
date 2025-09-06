# Step 1: Use official Python base image
FROM python:3.11-slim

# Step 2: Install FFmpeg and system dependencies
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Step 3: Set working directory
WORKDIR /app

# Step 4: Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy all project files
COPY . .

# Step 6: Set environment variables (optional)
ENV PYTHONUNBUFFERED=1

# Step 7: Start the bot
CMD ["python", "main.py"]
