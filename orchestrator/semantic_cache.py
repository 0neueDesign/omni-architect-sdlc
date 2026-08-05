import chromadb
from chromadb.utils import embedding_functions
import hashlib

# Initialize ChromaDB Client (Connecting to the local Docker container)
# In production, use the HttpClient pointing to the docker service
try:
    chroma_client = chromadb.HttpClient(host='localhost', port=8000)
except Exception:
    # Fallback to ephemeral memory for local testing without docker
    chroma_client = chromadb.Client()

# Use default embedding function (all-MiniLM-L6-v2) for speed and local execution
ef = embedding_functions.DefaultEmbeddingFunction()

# Create or get the cache collection
cache_collection = chroma_client.get_or_create_collection(
    name="omni_semantic_cache",
    embedding_function=ef
)

def check_cache(query: str, threshold: float = 0.15) -> str | None:
    """
    Checks if a highly similar query (e.g., CI error log or planning request)
    has been asked recently.
    Returns the cached response if similarity distance is below the threshold.
    """
    print(f"[Cache] Checking semantic cache for query... (Length: {len(query)})")
    try:
        results = cache_collection.query(
            query_texts=[query],
            n_results=1
        )
        
        if results and results['distances'][0]:
            distance = results['distances'][0][0]
            if distance < threshold:
                print(f"[+] Cache HIT! (Distance: {distance:.4f}) - Saving API Token Credits.")
                return results['documents'][0][0]
                
        print("[-] Cache MISS. Proceeding to API.")
        return None
    except Exception as e:
        print(f"[!] Cache Error: {e}")
        return None

def store_cache(query: str, response: str) -> None:
    """
    Stores a successful response in the semantic cache.
    Generates a deterministic ID based on the hash of the query.
    """
    try:
        # Use a stable hash across python restarts
        query_id = hashlib.md5(query.encode('utf-8')).hexdigest()
        cache_collection.add(
            documents=[response],
            metadatas=[{"type": "ci_resolution_or_summary"}],
            ids=[query_id]
        )
        print(f"[+] Stored successful response in Semantic Cache (ID: {query_id})")
    except Exception as e:
        print(f"[!] Failed to store in cache: {e}")

if __name__ == "__main__":
    # Test the Semantic Cache
    q1 = "Fix TypeError: undefined is not a function in src/App.js on line 42"
    a1 = "The issue is a missing import. Add `import { useState } from 'react';` to the top of the file."
    
    store_cache(q1, a1)
    
    # Simulate a slightly different query
    q2 = "TypeError: undefined is not a function in src/App.js line 42. How to fix?"
    cached_answer = check_cache(q2)
    print(f"Retrieved: {cached_answer}")
