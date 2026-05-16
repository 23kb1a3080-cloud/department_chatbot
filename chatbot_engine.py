# chatbot_engine.py
import chromadb
from sentence_transformers import SentenceTransformer

def run_chatbot():
    print("=" * 60)
    print("🎓 NBKR Institute Chatbot - ChromaDB Powered")
    print("=" * 60)
    
    # Load model
    print("\n🔄 Loading model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Connect to ChromaDB
    print("🔄 Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path="./chroma_db")
    
    try:
        collection = client.get_collection("college_data")
        print(f"✓ Connected to database with {collection.count()} documents\n")
    except:
        print("⚠ Database not found. Run embeddings.py first.")
        return
    
    print("Type 'exit' to quit\n")
    print("=" * 60)
    
    while True:
        query = input("\n💬 Ask Question: ").strip()
        
        if query.lower() in ['exit', 'quit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        if not query:
            continue
        
        # Create query embedding
        query_embedding = model.encode([query])[0]
        
        # Search in ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=3
        )
        
        print("\n" + "=" * 60)
        print("📝 ANSWER:")
        print("=" * 60)
        
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0], 1):
                print(f"\n{i}. {doc[:500]}...")  # Show first 500 chars
        else:
            print("\nNo relevant information found.")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    run_chatbot()
