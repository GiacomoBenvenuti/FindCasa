# Use Python 3.11 slim image as base
FROM python:3.11-slim AS base

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

# Configure Tor
RUN echo "SocksPort 9050" >> /etc/tor/torrc && \
    echo "ControlPort 9051" >> /etc/tor/torrc

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Development stage
FROM base AS development

# Install development tools
RUN apt-get update && apt-get install -y \
    git \
    vim \
    nano \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install additional Python development packages
RUN pip install --no-cache-dir \
    ipython \
    pytest \
    black \
    flake8

# Create a development startup script
RUN printf '#!/bin/bash\nservice tor start\nsleep 2\necho "Development environment ready! Tor is running."\necho "You can now attach VS Code to this container."\necho "To run the scraper: python main.py <search_url>"\ntail -f /dev/null\n' > /app/dev-start.sh && \
    chmod +x /app/dev-start.sh

# Default command for development
CMD ["/app/dev-start.sh"]

# Production stage
FROM base AS production

# Copy application files
COPY main.py extract_features.py utils.py ./

# Create a startup script to run Tor and the application
RUN printf '#!/bin/bash\nservice tor start\nsleep 5\npython main.py\n' > /app/start.sh && \
    chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"]