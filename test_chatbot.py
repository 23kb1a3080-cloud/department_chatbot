"""
Test script to verify the NLP-enhanced chatbot responses
"""

import requests
import json

def test_chatbot():
    """Test various queries to the chatbot."""
    
    print("=" * 70)
    print("🧪 Testing NBKR Institute AI Chatbot - NLP Enhanced")
    print("=" * 70)
    
    # Check health endpoint
    try:
        response = requests.get("http://localhost:8000/health")
        health = response.json()
        print(f"\n✓ Health Check:")
        print(f"  Status: {health['status']}")
        print(f"  Version: {health['version']}")
        print(f"  NLP Enabled: {health['nlp_enabled']}")
        print(f"  Knowledge Base Size: {health['knowledge_base_size']}")
    except Exception as e:
        print(f"\n✗ Health check failed: {e}")
        return
    
    # Test queries
    test_queries = [
        "Who is the HOD of AI & DS department?",
        "Tell me about Dr Narayana Rao Appini",
        "Which faculty teaches Machine Learning?",
        "What is the attendance system?",
        "How can I access e-journals?",
        "Tell me about admissions",
        "Who are the professors in AI department?",
        "What courses are available?",
    ]
    
    print("\n" + "=" * 70)
    print("📝 Test Queries:")
    print("=" * 70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 70)
        # Note: WebSocket testing would require a different approach
        # This is just to show the test queries
        print("   (Use the web interface to test these queries)")
    
    print("\n" + "=" * 70)
    print("✓ Chatbot is ready for testing!")
    print("📍 Open http://localhost:8000 in your browser")
    print("=" * 70)

if __name__ == "__main__":
    test_chatbot()
