# preprocess.py
import pandas as pd
import re
import os
import json

def clean_text(text):
    """Clean and normalize text"""
    text = str(text)
    text = re.sub(r"\n+", " ", text)  # Replace newlines with space
    text = re.sub(r"\s+", " ", text)  # Replace multiple spaces with single space
    text = re.sub(r"[^\w\s.,!?-]", "", text)  # Remove special characters
    text = text.strip()
    text = text.lower()
    return text

def preprocess_all_data():
    print("🔄 Preprocessing All Data...")
    
    all_cleaned_data = []
    
    # Process main website data
    if os.path.exists("data/raw/main_website.csv"):
        print("  Processing main website data...")
        df = pd.read_csv("data/raw/main_website.csv")
        df["cleaned"] = df["text"].apply(clean_text)
        df = df[df["cleaned"].str.len() > 10]  # Filter short texts
        df.to_csv("data/cleaned/cleaned_website.csv", index=False)
        all_cleaned_data.extend(df["cleaned"].tolist())
        print(f"    ✓ Cleaned {len(df)} website entries")
    
    # Process faculty data
    if os.path.exists("data/raw/faculty_data.csv"):
        print("  Processing faculty data...")
        df = pd.read_csv("data/raw/faculty_data.csv")
        df["cleaned"] = df["content"].apply(clean_text)
        df = df[df["cleaned"].str.len() > 20]
        df.to_csv("data/cleaned/cleaned_faculty.csv", index=False)
        all_cleaned_data.extend(df["cleaned"].tolist())
        print(f"    ✓ Cleaned {len(df)} faculty entries")
    
    # Process PDF data
    if os.path.exists("data/raw/academic_calendar.csv"):
        print("  Processing PDF data...")
        df = pd.read_csv("data/raw/academic_calendar.csv")
        df["cleaned"] = df["content"].apply(clean_text)
        df = df[df["cleaned"].str.len() > 20]
        df.to_csv("data/cleaned/cleaned_pdf.csv", index=False)
        all_cleaned_data.extend(df["cleaned"].tolist())
        print(f"    ✓ Cleaned {len(df)} PDF entries")
    
    # Process portal data
    if os.path.exists("data/raw/portal_data.csv"):
        print("  Processing portal data...")
        df = pd.read_csv("data/raw/portal_data.csv")
        if "content" in df.columns:
            df["cleaned"] = df["content"].apply(clean_text)
        elif "portal_content" in df.columns:
            df["cleaned"] = df["portal_content"].apply(clean_text)
        df = df[df["cleaned"].str.len() > 10]
        df.to_csv("data/cleaned/cleaned_portal.csv", index=False)
        all_cleaned_data.extend(df["cleaned"].tolist())
        print(f"    ✓ Cleaned {len(df)} portal entries")
    
    # Save combined cleaned data
    combined_df = pd.DataFrame({"text": all_cleaned_data})
    combined_df = combined_df.drop_duplicates()
    combined_df.to_csv("data/cleaned/all_cleaned_data.csv", index=False)
    
    # Save as JSON
    with open("data/cleaned/all_cleaned_data.json", "w", encoding="utf-8") as f:
        json.dump(all_cleaned_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Preprocessing Completed: {len(all_cleaned_data)} total entries")
    return all_cleaned_data

if __name__ == "__main__":
    preprocess_all_data()
