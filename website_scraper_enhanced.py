# website_scraper_enhanced.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

URL = "https://www.nbkrist.org/"

def scrape_main_website():
    print("🔄 Scraping Main Website...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        data = []
        
        # Extract from various tags
        for tag in soup.find_all(["p", "h1", "h2", "h3", "h4", "li", "a", "span"]):
            text = tag.get_text(strip=True)
            if len(text) > 5:
                data.append({
                    "text": text,
                    "tag": tag.name,
                    "class": tag.get("class", [])
                })
        
        # Save as CSV
        df = pd.DataFrame(data)
        df.to_csv("data/raw/main_website.csv", index=False)
        
        # Save as JSON
        with open("data/raw/main_website.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Main Website Data Saved: {len(data)} entries")
        return data
        
    except Exception as e:
        print(f"⚠ Error scraping main website: {e}")
        return []

if __name__ == "__main__":
    scrape_main_website()
