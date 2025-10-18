from time import sleep
import random
import json
import re
import os
import argparse

# from bs4 import BeautifulSoup
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import pandas as pd
import requests
from urllib.parse import urlparse, parse_qs

from utils import confirm_ip

proxies = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050',
}

# Generate a random User-Agent
ua = UserAgent()
headers = {
    "User-Agent": ua.random,
    'Accept-Language': 'en-US,en;q=0.9',
    # 'Accept-Encoding': 'gzip, deflate, br', # BAD!
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Connection': 'keep-alive',
    'DNT': '1',  # Do Not Track header
    'Upgrade-Insecure-Requests': '1',
    'Referer': 'https://www.google.com/',  # Fake a referer
}

# sleep(random.uniform(1,5))
# Example Rightmove listing URL (replace with real one)
# url = "https://www.rightmove.co.uk/properties/159634115#/"


def scrape(base_url, delay=1):
    session = requests.Session()
    session.headers.update(headers)
    session.proxies.update(proxies)
    # response = session.get(base_url, proxies=proxies, headers=headers, timeout=15)
    # print(response.text)

    properties = []
    page = 0
    while True:
        paged_url = f"{base_url}&index={page * 24}"  # Rgmv paginates with index=0,24,48,...
        print(f"[+] Scraping page {page + 1} — {paged_url}")
        try:
            res = session.get(paged_url, proxies=proxies, headers=headers, timeout=60)
            # print(res.text)
            if res.status_code != 200:
                print(f"[!] Failed to fetch page {page + 1}")
                break
        except Exception as e:
            print(f"[!] Error: {e}")
            break

        soup = BeautifulSoup(res.text, 'html.parser')
        listings = soup.find_all('div', class_='PropertyCard_propertyCardContainerWrapper__mcK1Z propertyCard-details')

        if not listings:
            print("[✓] No more listings found. Done.")
            break

        for card in listings:
            url = card.find('a', class_='propertyCard-link')['href']
            card_url = f"https://www.rightmove.co.uk{url}"  
            session.headers.update(headers)
            session.proxies.update(proxies)
            sleep(random.uniform(1, 3))          
            res1 = session.get(card_url, proxies=proxies, headers=headers, timeout=60)
            soup1 = BeautifulSoup(res1.text, 'html.parser')
            script_tag = soup1.find('script', text=re.compile(r'window\.PAGE_MODEL'))
                
            if script_tag:
                # Step 2: Extract the JavaScript content inside the <script> tag
                script_content = script_tag.string

                # Step 3: Use regex to find the JSON data after 'window.PAGE_MODEL ='
                matchh = re.search(r'window\.PAGE_MODEL = (\{.*\})', script_content)
                
                if matchh.group(1):
                    # Step 4: Parse the JSON data
                    tt = matchh.group(1)
                    tt = tt.replace("false", "False")
                    tt = tt.replace("true", "True")
                    tt = tt.replace("null", "0")
                    data = eval(tt)
                    
                    # remove some unecessary fields to save memory
                    bad_fields = ("metadata", "images", "staticMapImgUrls", "termsOfUse")
                    for field in bad_fields:
                        if field in data["propertyData"].keys():
                            del data["propertyData"][field]
                else:
                    continue

                file_name = f"data/id{data["propertyData"]["id"]}.json"
                
                if os.path.exists(file_name):
                    continue

                # Step 4: Save the dictionary to a JSON file with the 'id' as the filename
                with open(file_name, 'w') as json_file:
                    json.dump(data, json_file, indent=4)

        page += 1
        if delay:
                sleep(random.uniform(1, 3))

    return properties

def save_to_csv(properties, filename="rgmv_properties.csv"):
    df = pd.DataFrame(properties)
    df.to_csv(filename, index=False)
    print(f"[✓] Saved {len(df)} properties to {filename}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Scrape property listings from Rgmv using Tor proxy')
    parser.add_argument('base_url', 
                       help='The base URL for the Rgmv search results page')
    parser.add_argument('--delay', '-d', 
                       type=float, 
                       default=1, 
                       help='Delay between requests in seconds (default: 1)')
    
    args = parser.parse_args()
    
    # Check VPN is used 
    confirm_ip()

    scrape(args.base_url, delay=args.delay)

if __name__=="__main__":
    main()

