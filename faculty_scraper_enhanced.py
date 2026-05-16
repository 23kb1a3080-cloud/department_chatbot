# faculty_scraper.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

URL = "https://nbkrist.irins.org/faculty/index/Department+of++AI+and+DS"

def scrape_faculty():
    print("🔄 Scraping Faculty Data...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        faculty_data = []
        
        # Find all faculty cards/divs
        faculty_cards = soup.find_all("div", class_=lambda x: x and ("faculty" in x.lower() or "card" in x.lower()))
        
        if not faculty_cards:
            # Fallback: get all divs with substantial text
            faculty_cards = soup.find_all("div")
        
        for card in faculty_cards:
            text = card.get_text(strip=True)
            if len(text) > 30:
                faculty_data.append({
                    "content": text,
                    "html": str(card)[:500]  # First 500 chars of HTML
                })
        
        # Save as CSV
        df = pd.DataFrame(faculty_data)
        df.to_csv("data/raw/faculty_data.csv", index=False)
        
        # Also save as JSON
        with open("data/raw/faculty_data.json", "w", encoding="utf-8") as f:
            json.dump(faculty_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Faculty Data Saved: {len(faculty_data)} entries")
        return faculty_data
        
    except Exception as e:
        print(f"⚠ Error scraping faculty: {e}")
        return []

if __name__ == "__main__":
    scrape_faculty()
