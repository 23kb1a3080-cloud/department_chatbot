# embeddings.py
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
import os

def create_embeddings():
    print("🔄 Creating Embeddings and Vector Database...")
    
    # Load model
    print("  Loading sentence transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Load cleaned data
    if not os.path.exists("data/cleaned/all_cleaned_data.csv"):
        print("⚠ No cleaned data found. Run preprocess.py first.")
        return
    
    df = pd.read_csv("data/cleaned/all_cleaned_data.csv")
    texts = df["text"].tolist()
    
    print(f"  Creating embeddings for {len(texts)} documents...")
    embeddings = model.encode(texts, show_progress_bar=True)
    
    # Create ChromaDB client
    print("  Initializing ChromaDB...")
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Delete existing collection if it exists
    try:
        client.delete_collection("college_data")
    except:
        pass
    
    # Create new collection
    collection = client.create_collection(
        name="college_data",
        metadata={"description": "NBKR Institute knowledge base"}
    )
    
    # Add documents in batches
    print("  Adding documents to ChromaDB...")
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        batch_embeddings = embeddings[i:i+batch_size]
        batch_ids = [str(j) for j in range(i, i+len(batch_texts))]
        
        collection.add(
            documents=batch_texts,
            embeddings=batch_embeddings.tolist(),
            ids=batch_ids
        )
    
    print(f"✓ Embeddings Stored: {len(texts)} documents in ChromaDB")
    print(f"✓ Database location: ./chroma_db")
    
    return collection

if __name__ == "__main__":
    create_embeddings()
