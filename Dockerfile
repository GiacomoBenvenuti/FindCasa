# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tor \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create data directory
RUN mkdir -p /app/data

# Copy application files
COPY . .

# Configure Tor
RUN echo "SocksPort 9050" >> /etc/tor/torrc && \
    echo "ControlPort 9051" >> /etc/tor/torrc

# Expose any ports if needed (optional, for debugging)
# EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create a startup script to run Tor and the application
RUN echo '#!/bin/bash\n\
service tor start\n\
sleep 5\n\
python main.py\n' > /app/start.sh && \
chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"]