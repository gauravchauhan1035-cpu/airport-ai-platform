# Airport AI Platform

AI-powered Airport Operations Monitoring Platform — a local-first system that automatically routes questions to SQL (operational metrics) or RAG (SOP documents) agents.

> **Status:** Phase 1 complete — project scaffolding, Docker, FastAPI, and Next.js initialized.

## Architecture

```
Browser → Next.js Frontend → FastAPI Backend → Router Agent
                                    ├── SQL Agent → SQLite
                                    └── RAG Agent → FAISS
                                              ↓
                                          Ollama (llama3.1)
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, React Query, Axios |
| Backend | FastAPI, SQLAlchemy, Pydantic, JWT, RBAC |
| Database | SQLite |
| LLM | Ollama (llama3.1) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector Store | FAISS |
| Deployment | Docker Compose |

## Folder Structure

```
airport-ai-platform/
├── frontend/          # Next.js 15 application
├── backend/           # FastAPI application
│   └── app/
│       ├── api/       # Route handlers
│       ├── agents/    # Router, SQL, RAG agents
│       ├── services/  # Business logic
│       ├── rag/       # RAG pipeline
│       ├── database/  # DB session & models
│       ├── auth/      # JWT & RBAC
│       └── ...
├── data/
│   ├── pdfs/          # Uploaded PDF documents
│   ├── faiss/         # Vector index storage
│   ├── sqlite/        # SQLite database
│   └── logs/          # Application logs
├── docker/            # Dockerfiles
└── docker-compose.yml
```

## Quick Start

### Prerequisites

- Docker Desktop (with Docker Compose v2)
- 8GB+ RAM recommended (for Ollama + llama3.1)

### Setup

```bash
# Clone and enter project
cd airport-ai-platform

# Copy environment file
cp .env.example .env

# Build and start all services
docker compose up --build
```

### URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| Ollama | http://localhost:11434 |

## Development Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | ✅ Complete | Project scaffolding, Docker, FastAPI, Next.js |
| 2 | ✅ Complete | Database models, SQLite schema, seed data, repository |
| 3 | Pending | JWT authentication & RBAC |
| 4 | Pending | Metrics API |
| 5 | Pending | SQL Agent |
| 6 | Pending | RAG Pipeline |
| 7 | Pending | Router Agent |
| 8 | Pending | Frontend Integration |
| 9 | Pending | Testing |
| 10 | Pending | Optimization |

## License

Private — take-home assignment.
