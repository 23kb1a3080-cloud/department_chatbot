# portal_scraper.py
"""
Scrapes NBKR Student Portal using Playwright.
Handles dynamic JavaScript rendering, login forms, and SPA content.
"""

import asyncio
import json
import os
import pandas as pd
from playwright.async_api import async_playwright

URL = "https://portal.nbkrsac.in/"

async def scrape_portal_async():
    print("🔄 Scraping Student Portal (Playwright)...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        print(f"  Loading: {URL}")
        try:
            await page.goto(URL, wait_until="networkidle", timeout=30000)
        except Exception:
            await page.goto(URL, wait_until="domcontentloaded", timeout=30000)

        # Wait for JS to render
        await page.wait_for_timeout(4000)

        # Take screenshot for debugging
        os.makedirs("data/raw", exist_ok=True)
        await page.screenshot(path="data/raw/portal_screenshot.png")

        data = []

        # Extract all visible text elements
        for tag in ["h1", "h2", "h3", "p", "li", "a", "button", "label", "span", "td"]:
            elements = await page.query_selector_all(tag)
            for el in elements:
                try:
                    text = (await el.inner_text()).strip()
                    if len(text) > 5:
                        data.append({"tag": tag, "content": text})
                except Exception:
                    pass

        # Get full body text as fallback
        body_text = await page.inner_text("body")
        if body_text.strip():
            data.append({"tag": "body", "content": body_text.strip()[:3000]})

        # Get page title
        title = await page.title()
        if title:
            data.append({"tag": "title", "content": title})

        await browser.close()

    df = pd.DataFrame(data).drop_duplicates(subset="content")
    df.to_csv("data/raw/portal_data.csv", index=False)

    with open("data/raw/portal_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ Portal Data Saved: {len(df)} entries → data/raw/portal_data.csv")
    print(f"  Screenshot saved: data/raw/portal_screenshot.png")
    return data


def scrape_portal():
    return asyncio.run(scrape_portal_async())


if __name__ == "__main__":
    scrape_portal()
