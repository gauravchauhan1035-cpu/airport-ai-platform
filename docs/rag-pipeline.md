# RAG Pipeline Documentation

The Retrieval-Augmented Generation (RAG) pipeline enables the Airport AI Platform to accurately answer questions regarding internal policies, manuals, and standard operating procedures (SOPs) without fine-tuning the LLM. 

By executing a local search against uploaded PDFs, the platform maintains strict data privacy while providing contextually aware answers.

## High-Level RAG Architecture

```mermaid
graph TD
    subgraph Ingestion Pipeline (Upload)
        PDF[PDF Upload] --> Extractor[PyMuPDF Text Extractor]
        Extractor --> Chunker[LangChain RecursiveTextSplitter]
        Chunker --> Embedder1[sentence-transformers<br/>all-MiniLM-L6-v2]
        Embedder1 --> Index[(FAISS Vector Index)]
        Chunker --> SQLite[(SQLite Metadata Mapping)]
    end
    
    subgraph Retrieval Pipeline (Query)
        User[User Question] --> IntentRouter{Intent Router}
        IntentRouter -->|Classified as RAG| Embedder2[sentence-transformers]
        Embedder2 -->|Semantic Vector| Index
        Index -->|Top-K chunk IDs| SQLite
        SQLite -->|Raw text & Page numbers| RAGAgent[RAG Agent]
        RAGAgent -->|Prompt Generation| Ollama((Ollama llama3.2))
        Ollama -->|Final Answer + Citations| Aggregator[Aggregator Agent]
    end
```

## 1. Ingestion Phase

### PDF Text Extraction
When a user with Admin privileges uploads a PDF via the Knowledge Base UI, the backend utilizes **PyMuPDF (fitz)** to extract raw text on a per-page basis. This ensures that the page numbers are inherently tied to the extracted text for later citation.

### Chunking Strategy
The raw text is split into manageable chunks using a `RecursiveCharacterTextSplitter`.
- **Chunk Size: 500 characters** — This relatively small chunk size prevents the LLM context window from being overwhelmed by irrelevant text, keeping the retrieval precise.
- **Chunk Overlap: 50 characters** — A slight overlap ensures that concepts split across chunk boundaries maintain their semantic meaning.

### Embedding Model
The platform uses the **`all-MiniLM-L6-v2`** model from the `sentence-transformers` library.
- **Why this model?** It is highly optimized for speed and size, making it perfect for running locally on CPU. It produces a dense semantic vector of **384 dimensions**.

### FAISS Indexing & SQLite Mapping
The 384-dimensional vectors are stored locally in a flat **FAISS (Facebook AI Similarity Search)** index.
Simultaneously, the original raw text, the document ID, and the exact page number of each chunk are saved in the SQLite `document_chunks` table, keyed by a unique UUID that matches the FAISS index ID.

---

## 2. Retrieval Phase

### Top-K Semantic Search
When the Router determines a question requires the RAG Agent, the query is passed through the same `all-MiniLM-L6-v2` embedding model.
The FAISS index performs an L2 distance similarity search to find the closest matching vectors.
- **Top-K Parameter: 5** — The system retrieves the top 5 most semantically similar chunks.

### Metadata Reconstruction
The retrieved FAISS IDs are used to query the SQLite `document_chunks` table to rebuild the payload, attaching the raw textual context and the source page number.

### Prompt Creation & Answer Generation
The `RAGAgent` dynamically constructs a prompt containing:
1. Strict instructions forcing the LLM to only use the provided context.
2. The Top-5 text chunks.
3. The user's original question.

This prompt is sent to the local **Ollama instance (llama3.2)**.

### Citation Generation
To build trust with the airport staff, the response is synthesized alongside its source metadata. The Aggregator Agent ensures that if the RAG Agent found data, the final natural language answer explicitly states the document name and page number (e.g., *"According to the Baggage Handling SOP (Page 14), the conveyor belt must..."*).
