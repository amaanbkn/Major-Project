# How to Ingest Documents into RAG

This folder contains the source documents used for the Retrieval-Augmented Generation (RAG) vector database.

To ingest these documents into ChromaDB:

1. Ensure your `.env` file is set up with `GEMINI_API_KEY`.
2. From the `backend` directory, run the ingestion script:

```bash
python -m services.ingest --path ./documents/
```

This will chunk the text files, generate embeddings using the Gemini API, and store them in the ChromaDB collection located at `backend/chroma_data/`.
