FROM python:3.11-slim

# Install unrar for RAR support
RUN apt-get update && \
    apt-get install -y unrar && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot.py .

# Create temp directory
RUN mkdir -p /tmp/compress_bot

# Run the bot
CMD ["python", "-u", "bot.py"]
