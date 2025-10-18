

# FindCASA - Property Scraper

A Python application for scraping property listings from Rihtmve using Tor proxy for privacy.

## Quick Start with Docker (Recommended)

### Prerequisites
- Docker and Docker Compose installed on your system

### Run with Docker Compose
```bash
# Build the image
docker-compose build

# Run with a specific search URL
docker-compose run findcasa-scraper python main.py "YOUR_RGMV_SEARCH_URL"

# Example with Cambridge properties
docker-compose run findcasa-scraper python main.py "/path/to/search/listing"
```

### Run with Docker directly
```bash
# Build the image
docker build -t findcasa-scraper .

# Create data directory
mkdir -p ./data

# Run the container
docker run -v $(pwd)/data:/app/data findcasa-scraper
```

## Manual Setup (Alternative)

```bash
# Create virtual environment
python3 -m venv findcasa

# Activate virtual environment
source findcasa/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application with a search URL
python main.py "/path/to/search/listing"

# Optional: specify custom delay between requests
python main.py "YOUR_SEARCH_URL" --delay 2
```

## Usage

### Command Line Arguments

```bash
python main.py <base_url> [--delay SECONDS]
```

**Arguments:**
- `base_url` (required): The Rgmv search results URL
- `--delay` or `-d` (optional): Delay between requests in seconds (default: 1)

**Example URLs:**
- Cambridge properties under £800k: `"https://www.rgmv.co.uk/property-for-sale/find.html?searchLocation=Cambridge%2C%20Cambridgeshire&useLocationIdentifier=true&locationIdentifier=REGION%5E274&radius=0.0&maxPrice=800000&_includeSSTC=on&includeSSTC=true&index=0"`
- London properties: `"https://www.rgmv.co.uk/property-for-sale/find.html?searchLocation=London&useLocationIdentifier=true&locationIdentifier=REGION%5E87490"`

### Docker Usage

```bash
# Run with Docker Compose
docker-compose run findcasa-scraper python main.py "YOUR_SEARCH_URL"

# Run with Docker directly
docker run -v $(pwd)/data:/app/data findcasa-scraper python main.py "YOUR_SEARCH_URL"
```

## Data Output

The scraped data will be saved to the `./data` directory as JSON files with property IDs as filenames.

## Features

- Uses Tor proxy for anonymized scraping
- Handles pagination automatically
- Saves detailed property data as JSON files
- Skips already downloaded properties
- Random delays to avoid rate limiting

## Configuration

You can specify any Rgmv search URL as a command-line argument. To get a search URL:
1. Go to rgmv.co.uk
2. Set up your search filters (location, price range, property type, etc.)
3. Copy the URL from your browser
4. Use that URL as the argument when running the script
