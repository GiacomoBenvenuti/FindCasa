from time import sleep
import random
import json
import re
import os
import argparse

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import pandas as pd
import requests

from utils import confirm_ip
from config_loader import get_config


class RMVScraper:
    """A web scraper for RMV property listings."""
    
    def __init__(self):
        """Initialize the scraper with configuration and session settings."""
        self.config = get_config()
        self.proxies = self.config.get_tor_proxies()
        
        # Generate a random User-Agent
        ua = UserAgent()
        self.headers = self.config.get_http_headers()
        self.headers["User-Agent"] = ua.random
        
        # Initialize session
        self.session = None
    
    def _setup_session(self):
        """Set up the HTTP session with headers and proxies."""
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(self.proxies)
    
    def download_page(self, url, timeout):
        """Download a single webpage.
        
        Args:
            url (str): The URL to download.
            timeout (int): Request timeout in seconds.
            
        Returns:
            requests.Response or None: The HTTP response object, or None if
            failed.
        """
        try:
            response = self.session.get(
                url, proxies=self.proxies, headers=self.headers,
                timeout=timeout)
            if response.status_code == 200:
                return response
            else:
                status = response.status_code
                print(f"[!] Failed to fetch {url} - Status: {status}")
                return None
        except Exception as e:
            print(f"[!] Error downloading {url}: {e}")
            return None
    
    def download_property_page(self, card_url, property_timeout, delay_min,
                               delay_max):
        """Download a property detail page with delay.
        
        Args:
            card_url (str): The property page URL.
            property_timeout (int): Request timeout in seconds.
            delay_min (float): Minimum delay before request.
            delay_max (float): Maximum delay before request.
            
        Returns:
            requests.Response or None: The HTTP response object, or None if
            failed.
        """
        self.session.headers.update(self.headers)
        self.session.proxies.update(self.proxies)
        sleep(random.uniform(delay_min, delay_max))
        return self.download_page(card_url, property_timeout)

    def extract_listing_data(self, res: requests.Response) -> list:
        """Extract listing data from the HTML response.
        
        Args:
            res (requests.Response): The HTTP response object.

        Returns:
            list: A list of BeautifulSoup elements representing property listings.
        """
        soup = BeautifulSoup(res.text, 'html.parser')
        selector_path = 'selectors.property_cards.container'
        container_class = self.config.get(selector_path)
        listings = soup.find_all('div', class_=container_class)
        return listings

    def scrape(self, base_url, delay=1):
        """Scrape property listings from RMV search results.
        
        The input url is a page showing multiple property listings.
        Each listing links to a subpage with detailed property data in JSON 
        format (cards). We iterate through each listing card, access its 
        subpage, extract the JSON data, and save it to a file.
        
        Args:
            base_url (str): The base URL for the RMV search results page.
            delay (float): Delay between requests in seconds.
            
        Returns:
            list: A list of scraped property data dictionaries.
        
        """
        # Set up session
        self._setup_session()
        
        # Get configuration values
        page_size = self.config.get('url_patterns.pagination.page_size', 24)
        timeout = self.config.get('request_settings.timeouts.page_request', 60)
        property_timeout = self.config.get(
            'request_settings.timeouts.property_request', 60)
        delay_min = self.config.get(
            'request_settings.delays.between_requests_min', 1)
        delay_max = self.config.get(
            'request_settings.delays.between_requests_max', 3)
        
        properties = []
        page = 0
        while True:
            # RMV paginates with index=0,24,48,...
            paged_url = f"{base_url}&index={page * page_size}"
            print(f"[+] Scraping page {page + 1} — {paged_url}")
            
            # Download the search results page
            response = self.download_page(paged_url, timeout)
            if not response:
                break

            # Extract property listings from the page
            listings = self.extract_listing_data(response)

            if not listings:
                print("[✓] No more listings found. Done.")
                break
            
            print(f"[+] Found {len(listings)} properties on page {page + 1}")
            
            # Iterate through each listing card 
            for i, card in enumerate(listings, 1):
                print(f"[+] Processing property {i}/{len(listings)} on page {page + 1}")
                self._process_property_card(card, delay_min, delay_max, 
                                          property_timeout)

            page += 1
            
            # Add delay between pages
            if delay:
                page_delay_min = self.config.get(
                    'request_settings.delays.between_pages_min', 1)
                page_delay_max = self.config.get(
                    'request_settings.delays.between_pages_max', 3)
                sleep(random.uniform(page_delay_min, page_delay_max))

        return properties

    def _process_property_card(self, card, delay_min, delay_max, property_timeout):
        """Process a single property card: download and parse its data.
        
        Args:
            card (BeautifulSoup element): The property card element.
            delay_min (float): Minimum delay before request.
            delay_max (float): Maximum delay before request.
            property_timeout (int): Request timeout in seconds.
            
        Returns:
            bool: True if processed successfully, False otherwise.
        """
        try:
            # Find the property link URL
            link_selector = 'selectors.property_links.class'
            property_link_class = self.config.get(link_selector)
            url = card.find('a', class_=property_link_class)['href']
            base_site_url = self.config.get('website.base_url')
            card_url = f"{base_site_url}{url}"
            
            # Download the property page
            response = self.download_property_page(card_url, property_timeout,
                                                 delay_min, delay_max)
            if not response:
                return False
            
            # Parse the property data
            property_data = self._parse_property_json(response.text)
            if not property_data:
                return False
            
            # Save the property data
            return self._save_property_data(property_data)
            
        except Exception as e:
            print(f"[!] Error processing property card: {e}")
            return False

    def _parse_property_json(self, html_content):
        """Parse JSON data from property page HTML.
        
        Args:
            html_content (str): The HTML content of the property page.
            
        Returns:
            dict or None: Parsed property data, or None if parsing failed.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract JSON data from the <script> tag
        script_pattern = self.config.get('regex_patterns.page_model.pattern')
        script_tag = soup.find('script', text=re.compile(script_pattern))
        
        if not script_tag:
            print("[!] Could not find script tag with PAGE_MODEL")
            return None
        
        # Extract the JavaScript content inside the <script> tag
        script_content = script_tag.string
        
        # Use regex to find the JSON data after 'window.PAGE_MODEL ='
        pattern = self.config.get('regex_patterns.page_model.pattern')
        match = re.search(pattern, script_content)
        
        if not match or not match.group(1):
            print("[!] Could not extract JSON from script content")
            return None
        
        try:
            # Parse the JSON data
            json_text = match.group(1)
            
            # Apply JSON replacements from config
            replacements = self.config.get(
                'data_processing.json_replacements', [])
            for replacement in replacements:
                json_text = json_text.replace(replacement['from'], replacement['to'])
            
            data = eval(json_text)  # Note: eval() is not safe for production
            
            # Remove unnecessary fields to save memory
            excluded_fields = self.config.get(
                'data_processing.excluded_fields', [])
            for field in excluded_fields:
                if field in data["propertyData"].keys():
                    del data["propertyData"][field]
            
            return data
            
        except Exception as e:
            print(f"[!] Error parsing JSON data: {e}")
            return None

    def _save_property_data(self, property_data):
        """Save property data to JSON file.
        
        Args:
            property_data (dict): The property data dictionary.
            
        Returns:
            bool: True if saved successfully, False otherwise.
        """
        try:
            # Generate filename using pattern from config
            property_id = property_data['propertyData']['id']
            file_pattern = self.config.get(
                'file_patterns.property_json.pattern')
            file_name = file_pattern.format(property_id=property_id)
            
            if os.path.exists(file_name):
                print(f"[*] File {file_name} already exists, skipping")
                return False

            # Save the dictionary to a JSON file with the 'id' as filename
            with open(file_name, 'w') as json_file:
                json.dump(property_data, json_file, indent=4)
            
            print(f"[✓] Saved property {property_id} to {file_name}")
            return True
            
        except Exception as e:
            print(f"[!] Error saving property data: {e}")
            return False


def save_to_csv(properties, filename="rgmv_properties.csv"):
    df = pd.DataFrame(properties)
    df.to_csv(filename, index=False)
    print(f"[✓] Saved {len(df)} properties to {filename}")


def main():
    # Set up argument parser
    description = 'Scrape property listings from Rgmv using Tor proxy'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('base_url',
                        help='The base URL for the Rgmv search results page')
    parser.add_argument('--delay', '-d',
                        type=float,
                        default=1,
                        help='Delay between requests in seconds')
    
    args = parser.parse_args()
    
    # Check VPN is used
    confirm_ip()

    # Create scraper instance and run
    scraper = RMVScraper()
    scraper.scrape(args.base_url, delay=args.delay)


if __name__ == "__main__":
    main()

