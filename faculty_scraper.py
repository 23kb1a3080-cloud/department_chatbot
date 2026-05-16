# faculty_scraper.py
"""
Scrapes AI & DS Faculty data from NBKR IRINS portal using Playwright.
Handles JavaScript-rendered content that requests/BS4 cannot access.
"""

import asyncio
import json
import os
import pandas as pd
from playwright.async_api import async_playwright

URL = "https://nbkrist.irins.org/faculty/index/Department+of++AI+and+DS"

async def scrape_faculty_async():
    print("🔄 Scraping Faculty Data (Playwright)...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        print(f"  Loading: {URL}")
        await page.goto(URL, wait_until="networkidle", timeout=30000)

        # Wait for faculty cards to appear
        await page.wait_for_timeout(3000)

        faculty_data = []

        # Try to find faculty profile cards
        cards = await page.query_selector_all(".profile-card, .faculty-card, .card, [class*='faculty'], [class*='profile']")

        if cards:
            for card in cards:
                text = await card.inner_text()
                text = text.strip()
                if len(text) > 20:
                    faculty_data.append({"content": text})
        else:
            # Fallback: extract all meaningful text blocks
            blocks = await page.query_selector_all("div, article, section")
            for block in blocks:
                text = await block.inner_text()
                text = text.strip()
                if 30 < len(text) < 2000:
                    faculty_data.append({"content": text})

        # Also grab page title and headings
        headings = await page.query_selector_all("h1, h2, h3, h4")
        for h in headings:
            text = await h.inner_text()
            if text.strip():
                faculty_data.append({"content": f"[HEADING] {text.strip()}"})

        await browser.close()

    os.makedirs("data/raw", exist_ok=True)
    df = pd.DataFrame(faculty_data).drop_duplicates(subset="content")
    df.to_csv("data/raw/faculty_data.csv", index=False)

    with open("data/raw/faculty_data.json", "w", encoding="utf-8") as f:
        json.dump(faculty_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Faculty Data Saved: {len(df)} entries → data/raw/faculty_data.csv")
    return faculty_data


def scrape_faculty():
    return asyncio.run(scrape_faculty_async())


if __name__ == "__main__":
    scrape_faculty()
