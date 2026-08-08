# ClinIQ 🏥
### *One Timeline. Every Record. Smarter Clinical Decisions.*

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript)](https://typescriptlang.org)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.x-06B6D4?logo=tailwindcss)](https://tailwindcss.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

**ClinIQ** is an AI-powered Clinical Intelligence Platform that unifies fragmented patient records — lab reports, prescriptions, vitals, and clinical notes — into a single longitudinal patient timeline enriched by clinical AI.

Built for **Problem Statement 3.3: AI-Driven Patient Record Analysis and Monitoring**.

---

## Architecture

```
ClinIQ uses Clean Architecture + Domain-Driven Design (DDD)

hackathon/
├── backend/              Python 3.11 · FastAPI · SQLAlchemy · SQLite
│   └── app/
│       ├── api/          Versioned API gateway (v1)
│       ├── core/         Cross-cutting concerns (config, security, DI)
│       ├── database/     SQLAlchemy async engine + session
│       ├── modules/      DDD business modules (self-contained)
│       │   ├── auth/
│       │   ├── patients/
│       │   ├── ingestion/
│       │   ├── document_intelligence/
│       │   ├── clinical_engine/
│       │   ├── medicine_engine/
│       │   ├── timeline/
│       │   ├── analytics/
│       │   ├── ai_copilot/
│       │   └── dashboard/
│       ├── ai/           AI module placeholders (LLM, RAG, memory)
│       ├── shared/       Reusable schemas, middleware, utils
│       └── observability/ Structured logging, metrics, audit
│
└── frontend/             React 18 · Vite · TypeScript · TailwindCSS
    └── src/
        ├── features/     Feature-first page modules
        ├── components/   Shared UI components + chart library
        ├── contexts/     React contexts (auth, global, loading, error)
        ├── hooks/        Custom hooks
        ├── services/     Axios client + API endpoints
        ├── routes/       Router + route guards
        ├── layouts/      App and Auth layout shells
        ├── theme/        Design tokens (colors, typography, spacing)
        └── types/        Shared TypeScript interfaces
```

---

## Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Framework | FastAPI 0.111 |
| Language | Python 3.11 |
| ORM | SQLAlchemy 2.x (async) |
| Database | SQLite + aiosqlite |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt |
| Validation | Pydantic v2 |
| HTTP Client | httpx |
| Server | Uvicorn |
| Logging | structlog |
| Testing | pytest + pytest-asyncio |

### Frontend
| Layer | Technology |
|---|---|
| Framework | React 18 |
| Build | Vite |
| Language | TypeScript 5.x |
| Styling | TailwindCSS 3 |
| Components | shadcn/ui + Radix UI |
| Routing | React Router v6 |
| Forms | React Hook Form + Zod |
| HTTP | Axios |
| Charts | Recharts |
| Animation | Framer Motion |
| Icons | Lucide React |

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm 9+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
copy .env.example .env   # Windows
cp .env.example .env     # macOS/Linux

# Edit .env and set SECRET_KEY to a secure random value
# python -c "import secrets; print(secrets.token_hex(32))"

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000  
API Documentation: http://localhost:8000/docs  
Health Check: http://localhost:8000/api/v1/health

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment config
copy .env.example .env   # Windows
cp .env.example .env     # macOS/Linux

# Run development server
npm run dev
```

Frontend will be available at: http://localhost:5173

---

## Project Status

| Phase | Status | Description |
|---|---|---|
| Phase 0 | ✅ Complete | Software Foundation |
| Phase 1 | 🔄 Planned | Authentication + Patient CRUD |
| Phase 2 | 🔄 Planned | Document Upload + OCR |
| Phase 3 | 🔄 Planned | AI Clinical Intelligence |
| Phase 4 | 🔄 Planned | Timeline + Analytics |
| Phase 5 | 🔄 Planned | AI Copilot |

---

## Modules

| Module | Purpose |
|---|---|
| `auth` | JWT authentication, user management |
| `patients` | Patient registration and demographics |
| `ingestion` | Multi-document upload pipeline |
| `document_intelligence` | OCR + medical document parsing |
| `clinical_engine` | Lab analysis, trend detection, alerts |
| `medicine_engine` | Medication intelligence and timeline |
| `timeline` | Longitudinal patient event timeline |
| `analytics` | Population and individual analytics |
| `ai_copilot` | Natural language clinical assistant |
| `dashboard` | Clinician dashboard aggregation |

---

## Design Principles

- **Clean Architecture** — Dependency flows inward only
- **Domain-Driven Design** — Modules own their domain
- **SOLID** — Single responsibility throughout
- **DRY** — Shared logic lives in `core/` and `shared/`
- **Type Safety** — Pydantic v2 backend, strict TypeScript frontend
- **Security First** — JWT + bcrypt + CORS + input validation
- **Observability** — Structured logging + audit trail

---

## Team

Built for International Healthcare Hackathon 2026.

---

## License

MIT License — See [LICENSE](LICENSE) for details.
