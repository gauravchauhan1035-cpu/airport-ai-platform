# Architecture Decision Record (ADR)

This document captures the primary architectural decisions made during the design and implementation of the Airport AI Platform.

---

## 1. Web Frameworks

### Why FastAPI (Backend)?
- **Decision:** Use FastAPI for the backend API layer.
- **Reasoning:** AI and LLM workloads are heavily I/O bound (waiting for model generation or vector lookups). FastAPI’s native asynchronous architecture (`async/await`) ensures the main thread is never blocked during parallel agent execution. Additionally, Pydantic provides automatic request validation, which is critical for securing AI endpoints against malformed inputs.

### Why Next.js (Frontend)?
- **Decision:** Use Next.js 15 (App Router) with React.
- **Reasoning:** Next.js provides robust Server-Side Rendering (SSR) capabilities, making the initial dashboard load faster. The extensive ecosystem around React (Tailwind CSS, shadcn/ui, React Query) enabled rapid prototyping of complex UI components like the chat interface and paginated data tables.

---

## 2. Data Storage

### Why SQLite?
- **Decision:** Use SQLite for relational data (metrics, users, metadata).
- **Reasoning:** For an on-premise, localized deployment without complex cluster management, SQLite is sufficient. It requires zero configuration, stores data in a single mountable file, and handles the relatively low-concurrency read/write operations required by the current scope perfectly.

### Why FAISS?
- **Decision:** Use Facebook AI Similarity Search (FAISS) for the vector store.
- **Reasoning:** We needed a vector store that operates entirely offline and doesn't require a heavy separate database server (like Milvus or Pinecone). FAISS runs entirely in-memory and serializes to disk, offering blazingly fast L2 distance searches for our local RAG pipeline.

---

## 3. AI & Machine Learning Stack

### Why Ollama?
- **Decision:** Use Ollama as the local LLM serving engine.
- **Reasoning:** Running LLMs locally ensures strict data privacy—a hard requirement for enterprise airport operational data. Ollama provides a Dockerized, API-compatible layer over `llama.cpp`, heavily simplifying the deployment and hardware management of the `llama3.2` model.

### Why Sentence Transformers (`all-MiniLM-L6-v2`)?
- **Decision:** Use `sentence-transformers` for document embedding instead of an LLM.
- **Reasoning:** The `all-MiniLM-L6-v2` model is incredibly lightweight (under 100MB) and operates efficiently on a standard CPU. Generating vectors via this model is vastly faster than querying an LLM to generate embeddings, dramatically speeding up the PDF ingestion pipeline.

---

## 4. AI Workflow & Strategy

### Why our chunking strategy (Size: 500, Overlap: 50)?
- **Decision:** Split PDFs into 500-character chunks with a 50-character overlap.
- **Reasoning:** Smaller chunk sizes are required because `llama3.2` (the 3B parameter version) has a limited effective context window and can struggle with "lost in the middle" hallucination issues if fed massive walls of text. A 50-character overlap ensures words and sentences cut across boundaries maintain their semantic meaning.

### Why a Multi-Agent Routing approach?
- **Decision:** Use an Intent Router to classify and dispatch to specialized agents (SQL, RAG, Chat), rather than a single monolithic prompt.
- **Reasoning:** LLMs perform much better on complex tasks when the task is narrowed. By splitting the logic, the LLM generating SQL queries isn't distracted by procedural document rules, and the LLM generating natural language answers isn't trying to write SQL logic. The router guarantees strict separation of concerns.

---

## 5. Deployment & Security

### Why Docker Compose?
- **Decision:** Containerize all services and orchestrate via Docker Compose.
- **Reasoning:** Replicating the exact environment (Node, Python, Ollama, SQLite) natively across different OS environments is highly error-prone. Docker guarantees the app behaves exactly the same on the developer's laptop as it does in production.

### Why JWT (JSON Web Tokens)?
- **Decision:** Use stateless JWTs for authentication.
- **Reasoning:** JWTs remove the need for database lookups on every API request. The frontend stores the token and passes it in headers, enabling rapid Role-Based Access Control (RBAC) validation directly via FastAPI middleware.

---

## 6. Trade-offs & Future Improvements

**Trade-offs Considered:**
1. **SQLite Concurrency:** SQLite locks the database during writes. If the platform scaled to thousands of concurrent airport staff updating metrics simultaneously, SQLite would become a bottleneck.
2. **FAISS Scalability:** Flat FAISS indexes load entirely into RAM. While fine for hundreds of manuals, it would require significant memory for tens of thousands of documents.

**Future Improvements:**
- **Migrate to PostgreSQL + pgvector:** Moving to Postgres would resolve SQLite's write-concurrency limits and allow us to deprecate FAISS in favor of `pgvector`, unifying relational data and vector data in a single enterprise database.
- **Agent Framework Integration:** As workflows become more complex (e.g. agents querying other agents recursively), we should migrate our custom orchestration logic to a standardized framework like `LangGraph` or `AutoGen`.
