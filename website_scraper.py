# website_scraper.py
"""
Scrapes NBKR main website using Playwright.
Handles dynamic content, lazy-loaded sections, and JavaScript rendering.
"""

import asyncio
import json
import os
import pandas as pd
from playwright.async_api import async_playwright

URL = "https://www.nbkrist.org/"

async def scrape_main_website_async():
    print("🔄 Scraping Main Website (Playwright)...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        print(f"  Loading: {URL}")
        await page.goto(URL, wait_until="networkidle", timeout=30000)

        # Scroll to trigger lazy loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1000)

        data = []

        # Extract text from all meaningful tags
        for tag in ["h1", "h2", "h3", "h4", "p", "li", "a", "span", "td", "th"]:
            elements = await page.query_selector_all(tag)
            for el in elements:
                text = (await el.inner_text()).strip()
                href = await el.get_attribute("href") if tag == "a" else None
                if len(text) > 5:
                    entry = {"tag": tag, "text": text}
                    if href:
                        entry["href"] = href
                    data.append(entry)

        # Also grab meta description
        meta = await page.query_selector('meta[name="description"]')
        if meta:
            desc = await meta.get_attribute("content")
            if desc:
                data.append({"tag": "meta", "text": desc})

        await browser.close()

    os.makedirs("data/raw", exist_ok=True)
    df = pd.DataFrame(data).drop_duplicates(subset="text")
    df.to_csv("data/raw/main_website.csv", index=False)

    with open("data/raw/main_website.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ Main Website Data Saved: {len(df)} entries → data/raw/main_website.csv")
    return data


def scrape_main_website():
    return asyncio.run(scrape_main_website_async())


if __name__ == "__main__":
    scrape_main_website()
