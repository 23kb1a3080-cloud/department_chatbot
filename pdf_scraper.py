# pdf_scraper.py
"""
Downloads and extracts text from NBKR PDF documents using pdfplumber.
Also uses Playwright to discover PDF links from the website.
"""

import asyncio
import json
import os
import requests
import pdfplumber
import pandas as pd
from playwright.async_api import async_playwright

PDF_URL = "https://nbkrist.org/Acdemic_calendar/II,III&IVB.Tech.ISem.2025.pdf"

async def discover_pdf_links_async(base_url="https://www.nbkrist.org/"):
    """Use Playwright to find all PDF links on the website."""
    print("  Discovering PDF links on website...")
    pdf_links = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(base_url, wait_until="networkidle", timeout=30000)

        # Find all anchor tags with .pdf href
        links = await page.query_selector_all("a[href*='.pdf'], a[href*='PDF']")
        for link in links:
            href = await link.get_attribute("href")
            text = (await link.inner_text()).strip()
            if href:
                full_url = href if href.startswith("http") else f"https://www.nbkrist.org/{href.lstrip('/')}"
                pdf_links.append({"url": full_url, "label": text})

        await browser.close()

    print(f"  Found {len(pdf_links)} PDF links")
    return pdf_links


def download_and_extract_pdf(url: str, filename: str) -> list:
    """Download a PDF and extract its text page by page."""
    os.makedirs("data/raw", exist_ok=True)
    filepath = f"data/raw/{filename}"

    print(f"  Downloading: {url}")
    try:
        response = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        response.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"  Saved: {filepath}")
    except Exception as e:
        print(f"  ⚠ Download failed: {e}")
        return []

    # Extract text
    extracted = []
    try:
        with pdfplumber.open(filepath) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    extracted.append({
                        "page": i + 1,
                        "content": text.strip(),
                        "source": filename
                    })
        print(f"  Extracted {len(extracted)} pages of text")
    except Exception as e:
        print(f"  ⚠ Extraction failed: {e}")

    return extracted


def scrape_pdf():
    print("🔄 Scraping PDF Documents (Playwright + pdfplumber)...")

    all_extracted = []

    # 1. Extract the known academic calendar PDF
    data = download_and_extract_pdf(PDF_URL, "academic_calendar.pdf")
    all_extracted.extend(data)

    # 2. Discover more PDFs from the website
    try:
        pdf_links = asyncio.run(discover_pdf_links_async())
        for i, link in enumerate(pdf_links[:5]):  # Limit to first 5 discovered PDFs
            fname = f"discovered_pdf_{i+1}.pdf"
            extra = download_and_extract_pdf(link["url"], fname)
            all_extracted.extend(extra)
    except Exception as e:
        print(f"  ⚠ PDF discovery failed: {e}")

    # Save results
    df = pd.DataFrame(all_extracted)
    df.to_csv("data/raw/academic_calendar.csv", index=False)

    with open("data/raw/academic_calendar.json", "w", encoding="utf-8") as f:
        json.dump(all_extracted, f, indent=2, ensure_ascii=False)

    print(f"✓ PDF Data Extracted: {len(all_extracted)} pages → data/raw/academic_calendar.csv")
    return all_extracted


if __name__ == "__main__":
    scrape_pdf()
