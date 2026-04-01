from services.rag import get_collection
try:
    c = get_collection()
    print("chromadb success:", c.count())
except Exception as e:
    print("chromadb error:", e)
