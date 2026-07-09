# Airport AI Platform

An AI-powered Airport Operations Monitoring Platform — a local-first, multi-agent system that monitors live airport metrics and intelligently routes questions to the right data source automatically.

## Architecture

```
Browser
  └── Next.js Frontend (React, TypeScript, Tailwind CSS)
         └── FastAPI Backend
                └── WorkflowOrchestrator
                       ├── IntentRouter (Ollama: llama3.2)
                       │     └── Classifies question → produces execution plan
                       │
                       ├── SQL Agent (Ollama: llama3.2)
                       │     └── Converts natural language → SQL → SQLite DB
                       │
                       ├── RAG Agent (sentence-transformers + FAISS)
                       │     └── Semantic search over uploaded PDF documents
                       │
                       ├── Chat Agent (Ollama: llama3.2)
                       │     └── General conversation & reasoning
                       │
                       └── Aggregator Agent (Ollama: llama3.2)
                             └── Merges all agent outputs into one final answer
                                       ↓
                             Ollama (llama3.2) — Local LLM engine
                             powers ALL agents (Router, SQL, Chat, Aggregator)
```

### How the Orchestrator Works

1. A user asks a question in the **AI Assistant** tab.
2. The **WorkflowOrchestrator** receives the question and fetches conversation history.
3. The **IntentRouter** (powered by Ollama) reads the question and produces a JSON execution plan deciding which agents to run: `SQL`, `RAG`, `CHAT`, or any combination.
4. The selected agents are executed **in parallel** for speed.
5. The **AggregatorAgent** (powered by Ollama) merges all results into one coherent natural language answer.
6. The answer and context are saved to conversation memory for multi-turn chat.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, React Query, Axios |
| Backend | FastAPI, SQLAlchemy, Pydantic, JWT, RBAC |
| Database | SQLite |
| LLM Engine | Ollama running llama3.2 (local, no API key needed) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector Store | FAISS |
| Deployment | Docker Compose (4 containers) |

## User Roles

| Role | Access |
|------|--------|
| **Admin** | Full access — Dashboard (with Service Status), Metrics, AI Assistant, Knowledge Base, Settings |
| **Analyst** | Dashboard, Metrics, AI Assistant |
| **Viewer** | Dashboard, Metrics (read-only) |

## Folder Structure

```
airport-ai-platform/
├── frontend/          # Next.js 15 application
├── backend/           # FastAPI application
│   └── app/
│       ├── api/           # Route handlers (health, metrics, auth, query, documents)
│       ├── agents/        # Orchestrator, Router, SQL, Chat, Aggregator agents
│       ├── rag/           # RAG pipeline (PDF extraction, chunking, embedding, FAISS)
│       ├── services/      # LLM service (Ollama), Memory service
│       ├── prompts/       # System prompts for each agent
│       ├── database/      # DB session, models, seed data
│       ├── auth/          # JWT & RBAC
│       └── repositories/  # Data access layer
├── data/
│   ├── pdfs/          # Uploaded PDF documents
│   ├── faiss/         # FAISS vector index storage
│   ├── sqlite/        # SQLite database
│   └── logs/          # Application logs
├── docker-compose.yml
└── .env.example
```

## Quick Start

### Prerequisites

- Docker Desktop (with Docker Compose v2)
- 8 GB RAM minimum (Ollama + llama3.2 + application services)

### Setup

```bash
# Clone the repository
git clone https://github.com/gauravchauhan1035-cpu/airport-ai-platform.git
cd airport-ai-platform

# Copy environment file
cp .env.example .env

# Build and start all services (first run pulls llama3.2 — may take a few minutes)
docker compose up --build -d
```

### Services & URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| Ollama | http://localhost:11434 |

### Default Login Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | Admin!2026#ChangeMeNow | Admin |
| analyst | Analyst!2026#ChangeMeNow | Analyst |
| viewer | Viewer!2026#ChangeMeNow | Viewer |

> ⚠️ Change default passwords immediately in any production deployment.

## Docker Containers

| Container | Purpose |
|-----------|---------|
| `airport-ollama` | Runs the local Ollama LLM server |
| `airport-ollama-init` | One-time init container — pulls llama3.2 model |
| `airport-backend` | FastAPI application server |
| `airport-frontend` | Next.js production server |

## License

Private — All rights reserved. Gaurav Chauhan, 2026.
