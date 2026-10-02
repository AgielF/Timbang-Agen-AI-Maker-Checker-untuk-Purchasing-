# Timbang

> **AI Maker–Checker for Fraud-Resistant Procurement** — catching inflated prices and SOP violations before payment is approved.

[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063.svg)](https://docs.pydantic.dev/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![Langflow](https://img.shields.io/badge/Langflow-integrated-orange.svg)](https://langflow.org/)
[![Tests](https://img.shields.io/badge/tests-39%20passing-brightgreen.svg)](#testing)
[![ruff](https://img.shields.io/badge/lint-ruff-purple.svg)](https://docs.astral.sh/ruff/)
[![black](https://img.shields.io/badge/format-black-black.svg)](https://black.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Table of Contents

- [Ringkasan](#ringkasan)
- [Background](#background)
- [What is Timbang](#what-is-timbang)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Usage](#usage)
- [Testing](#testing)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Ringkasan

**Timbang** adalah sistem AI *Maker–Checker* untuk deteksi fraud pengadaan (procurement) di perusahaan menengah Indonesia yang belum memiliki ERP. Nama "Timbang" diambil dari kata Bahasa Indonesia yang berarti *menimbang* — proses mempertimbangkan secara cermat sebelum mengambil keputusan.

Fraud pengadaan merupakan salah satu bentuk kecurangan bisnis paling umum di Indonesia. Menurut ACFE (2026), kerugian rata-rata akibat fraud pengadaan mencapai ~5% dari pendapatan tahunan perusahaan. Tanpa sistem ERP, staf purchasing sering kali harus memeriksa penawaran vendor, dokumen PO, dan invoice secara manual — proses yang lambat, rawan human error, dan mudah dimanipulasi.

Timbang menyelesaikan masalah ini dengan dua agen AI yang bekerja berpasangan: **Maker Agent** menganalisis penawaran vendor, melakukan cross-validasi harga dengan data pasar terkini, dan memberikan rekomendasi vendor terbaik. **Checker Agent** kemudian melakukan three-way matching (PO–GR–Invoice), validasi SOP, dan menghasilkan laporan risiko sebelum pembayaran disetujui.

Status proyek untuk IBM SkillsBuild Hackathon 2026: **Maker Agent** sudah end-to-end (endpoint `/recommend` menghasilkan HTTP 200, respons Langflow ~62.9 detik). **Checker Agent** sudah tersedia di backend (three-way matching, validasi SOP, laporan risiko — 39 tests pass), namun integrasi Langflow-nya masih dalam pengerjaan untuk fase berikutnya.

---

## Background

Mid-sized Indonesian companies — those generating between IDR 10 billion and IDR 500 billion annually — typically lack the ERP systems that larger corporations use to automate procurement controls. Their purchasing teams manage vendor quotes, purchase orders, goods receipts, and invoices through spreadsheets and email, creating multiple blind spots that fraudsters exploit:

- **Price inflation** — vendors quote above market rates, relying on the absence of automated benchmarking.
- **Fictitious vendors** — payments approved to shell companies with no goods delivered.
- **Document manipulation** — invoice amounts altered after goods receipt.
- **SOP bypass** — high-value transactions approved without required secondary sign-off.

Timbang addresses these gaps by automating the analytical work of a procurement auditor, running checks in near-real-time at the moment quotes and invoices are submitted.

---

## What is Timbang

Timbang is a **modular monolith** FastAPI backend that orchestrates two AI agents:

| Module | Agent Role | Responsibility | Key Output |
|---|---|---|---|
| `procurement` | **Maker Agent** | Vendor analysis, cross-price validation against market data, Langflow-powered recommendation | Ranked vendor recommendation + estimated savings |
| `audit` | **Checker Agent** | Three-way matching (PO/GR/Invoice), SOP rule validation, risk report generation | Risk report + compliance status |

Both modules share a common infrastructure layer (`shared/`) that handles configuration, database sessions, structured logging, rate limiting, and security middleware.

---

## Architecture

```
router → service → repository → model
```

- **router** — HTTP boundary: Pydantic validation, rate limiting, exception mapping to HTTP codes.
- **service** — Business logic and orchestration; calls repositories and external agents (Langflow).
- **repository** — The only layer that touches SQLAlchemy sessions directly.
- **model** — SQLAlchemy 2.0 ORM entities and Pydantic schemas.

No layer may import upward (reversed dependency is forbidden). Each module exposes exactly one import surface: `public_api.py`.

```
[User: Purchasing / Finance Staff]
            │
            ▼
[Frontend React]  ──(REST)──▶  [Backend FastAPI]
                                    │
                                    ├──▶ [PostgreSQL 16]
                                    ├──▶ [Redis]  (rate limit)
                                    ├──▶ [9Router] ──▶ [LLM Providers]
                                    └──▶ [Langflow] (Maker & Checker flow)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full C4 container diagram and architecture decision records.

---

## Tech Stack

| Layer | Library / Tool | Version | Notes |
|---|---|---|---|
| Web framework | FastAPI | ≥ 0.115 | Async, OpenAPI auto-docs |
| Validation | Pydantic v2 + pydantic-settings | ≥ 2.9 / 2.6 | 12-Factor config |
| ORM | SQLAlchemy async | 2.0 | asyncpg driver |
| Migrations | Alembic | ≥ 1.14 | deferred for hackathon |
| Rate limiting | slowapi | ≥ 0.1.9 | Redis-backed in prod |
| Auth | python-jose | ≥ 3.3 | JWT HS256 (scaffolded) |
| Logging | structlog | ≥ 24.4 | JSON in prod |
| HTTP client | httpx | ≥ 0.28 | Langflow calls |
| Agent flow | Langflow + 9Router | — | Maker Agent wired; Checker deferred |
| Lint / format | ruff + black | ≥ 0.8 / 24.10 | CI-ready |
| Tests | pytest + pytest-asyncio | ≥ 8.3 / 0.24 | 39 tests |

**Deferred for hackathon deadline:** PostgreSQL in prod, Redis rate-limit backend, Docker, JWT runtime enforcement, Checker Agent Langflow flow.

---

## Repository Structure

```
project/
├── .env.example            # Config template — copy to .env, fill in secrets
├── .gitignore              # Sectioned; secrets, caches, DB files excluded
├── AGENTS.md               # AI agent operating contract
├── LICENSE                 # MIT © 2026 Agiel Fernanda
├── README.md               # This file
├── docs/
│   ├── ARCHITECTURE.md     # C4 diagram, layer rules, ADRs
│   ├── SECURITY.md         # OWASP controls, secret handling, commit checklist
│   └── agents/
│       └── BACKEND_AGENTS.md  # Coding rules for AI agents working on backend/
├── tools/
│   └── sanitize.sh         # Pre-commit secret scanner
├── scripts/
│   └── list_deps.sh        # Print Python env info + pip freeze
├── langflow/               # Langflow flow exports (not committed — .gitignored)
└── backend/
    ├── pyproject.toml      # Build, dependencies, ruff/black/pytest config
    ├── requirements.txt    # Frozen pip freeze from .venv
    └── src/timbang/
        ├── main.py         # FastAPI factory (create_app)
        ├── shared/
        │   ├── core/       # config, exceptions, logging, middleware
        │   └── db/         # async engine, session factory, declarative base
        ├── modules/
        │   ├── procurement/  # Maker Agent — models, schemas, repo, service, router
        │   └── audit/        # Checker Agent — models, schemas, repo, service, router
        ├── scripts/
        │   └── seed.py     # Idempotent demo data seeder
        └── tests/          # 39 tests (service, E2E, rate-limit, Langflow)
```

---

## Getting Started

### Prerequisites

- Python ≥ 3.12 (tested on 3.14)
- A running PostgreSQL 16 instance **or** SQLite for local development
- Redis (optional for dev — rate limiting falls back to in-memory)
- Langflow instance with the Maker Agent flow loaded (for `/recommend` endpoint)

### Installation

```bash
git clone https://github.com/<your-org>/timbang.git
cd timbang

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install backend with dev extras
cd backend
pip install -e ".[dev]"
```

Alternatively, install from the frozen requirements file:

```bash
pip install -r backend/requirements.txt
```

### Environment Variables

Copy `.env.example` to `.env` and fill in each value. **Never commit `.env`.**

| Variable | Description |
|---|---|
| `APP_NAME` | Application display name |
| `APP_ENV` | Runtime environment: `dev`, `staging`, or `prod` |
| `DEBUG` | Enable debug mode and `/docs` Swagger UI |
| `DATABASE_URL` | Async SQLAlchemy URL (`postgresql+asyncpg://...` or `sqlite+aiosqlite://...`) |
| `REDIS_URL` | Redis connection URL (rate limiting in production) |
| `JWT_SECRET` | Secret key for JWT signing — set a long random string |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiry window (default: 30) |
| `ROUTER_BASE_URL` | 9Router base URL for LLM routing |
| `ROUTER_API_KEY` | 9Router API key |
| `CORS_ORIGINS` | Comma-separated allowed origins (e.g. `http://localhost:5173`) |
| `LANGFLOW_BASE_URL` | Langflow server URL |
| `LANGFLOW_API_KEY` | Langflow API key (optional if auth disabled) |
| `LANGFLOW_MAKER_FLOW_ID` | UUID of the Maker Agent flow in Langflow |
| `LANGFLOW_TIMEOUT_SECONDS` | HTTP timeout for Langflow calls (default: 120) |

### Seeding the Database

```bash
# From project root, with .venv activated
python3 -m timbang.scripts.seed
```

Override the database URL for seeding:

```bash
SEED_DATABASE_URL=sqlite+aiosqlite:///demo.db python3 -m timbang.scripts.seed
```

### Running the API

```bash
# From project root, with .venv activated
uvicorn timbang.main:app --reload --app-dir backend/src
```

The API will be available at `http://localhost:8000`. When `DEBUG=true`, Swagger UI is served at `http://localhost:8000/docs`.

### Dependencies

Print the current Python environment and all installed packages:

```bash
./scripts/list_deps.sh
```

Or inspect the frozen snapshot directly:

```bash
cat backend/requirements.txt
```

---

## API Reference

All endpoints are prefixed under `/api/v1/` except `/health`.

| Method | Path | Description | Rate Limit |
|---|---|---|---|
| `GET` | `/health` | Service health check | None |
| `GET` | `/api/v1/procurement/vendors` | List all registered vendors | 120/min |
| `POST` | `/api/v1/procurement/vendors` | Register a new vendor | 30/min |
| `POST` | `/api/v1/procurement/vendors/{vendor_id}/quotes` | Submit a price quote for a vendor | 60/min |
| `GET` | `/api/v1/procurement/items/{item_name}/validate` | Cross-validate prices across all vendor quotes | 60/min |
| `GET` | `/api/v1/procurement/items/{item_name}/recommend` | **Maker Agent** — LLM-powered vendor recommendation via Langflow | 10/min |
| `POST` | `/api/v1/audit/findings` | Create a new audit finding | 60/min |
| `GET` | `/api/v1/audit/findings/{finding_id}` | Retrieve a single audit finding | 120/min |
| `POST` | `/api/v1/audit/transactions/{transaction_id}/match` | **Checker Agent** — Three-way matching (PO / GR / Invoice) | 60/min |
| `POST` | `/api/v1/audit/transactions/{transaction_id}/risk-report` | **Checker Agent** — Generate full risk report for a transaction | 10/min |

### Example: Maker Agent Recommendation

```bash
curl -X GET \
  "http://localhost:8000/api/v1/procurement/items/laptop/recommend" \
  -H "Accept: application/json"
```

> ⏱ **Note:** This endpoint calls Langflow synchronously. Expect a response time of approximately 60 seconds when the LLM is cold. Ensure `LANGFLOW_TIMEOUT_SECONDS` is set to at least `120`.

---

## Usage

A typical end-to-end procurement audit flow:

1. **Register vendors** — `POST /api/v1/procurement/vendors` for each vendor participating in the tender.
2. **Submit quotes** — `POST /api/v1/procurement/vendors/{vendor_id}/quotes` for each item quote received.
3. **Validate prices** — `GET /api/v1/procurement/items/{item_name}/validate` to cross-check quotes; outliers (> 30% from median) are flagged.
4. **Get recommendation** — `GET /api/v1/procurement/items/{item_name}/recommend` calls the Maker Agent (Langflow) for an AI-powered vendor recommendation with market-price citations.
5. **Three-way match** — `POST /api/v1/audit/transactions/{id}/match` after goods are received; compares PO, Goods Receipt, and Invoice (tolerances: qty ±2%, amount ±1%).
6. **Generate risk report** — `POST /api/v1/audit/transactions/{id}/risk-report` for the full Checker Agent report including SOP compliance (e.g. transactions > IDR 100,000,000 require level-2 approval).

---

## Testing

```bash
cd backend
pytest -q
```

**Current status: 39 tests pass, 0 failures, 0 skipped.**

Test coverage:

| File | Scope |
|---|---|
| `test_health.py` | Health endpoint |
| `test_procurement_service.py` | Cross-validate, register vendor, submit quote |
| `test_audit_service.py` | Three-way matching, SOP validation, risk report |
| `test_e2e_smoke.py` | Full HTTP cycle via `httpx.AsyncClient` |
| `test_rate_limit.py` | Rate limit enforcement (429 responses) |
| `test_procurement_langflow.py` | Langflow integration (mocked HTTP) |

Run with coverage:

```bash
pytest --cov=timbang --cov-report=term-missing -q
```

---

## Security

- All secrets are injected via environment variables — never hardcoded. See [docs/SECURITY.md](docs/SECURITY.md).
- Run `./tools/sanitize.sh` before every commit to scan for accidentally staged secrets.
- `.env`, `*.key`, `mcp.json`, `.bob/` are permanently `.gitignore`d.
- Rate limiting is enforced per IP address on every endpoint (slowapi + Redis in production).
- Security headers applied to every response: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`.
- CORS origins are explicitly allowlisted via `CORS_ORIGINS` env var.
- Stack traces never leak to production API responses — domain exceptions are mapped to HTTP codes in the router layer.
- OWASP API Security Top 10 (2023) controls documented in [docs/SECURITY.md](docs/SECURITY.md).

---

## Contributing

This repository is developed under a competitive hackathon deadline (**IBM SkillsBuild University Education National Hackathon 2026 — Hacktiv8 × IBM**, due 4 October 2026). External contributions are closed during this period.

After the competition, contributions are welcome. Please open an issue first to discuss what you would like to change, and follow the [Conventional Commits](https://www.conventionalcommits.org/) format.

---

## License

MIT © 2026 Agiel Fernanda. See [LICENSE](LICENSE).

---

## Acknowledgments

- **IBM SkillsBuild** and **Hacktiv8** — for organising the competition and providing the challenge brief.
- **Langflow** — for making LLM agent orchestration accessible without infrastructure overhead.
- **FastAPI** (Sebastián Ramírez) — for the best async Python web framework available.
- **Pydantic** — for making data validation a first-class citizen in Python.
- **SQLAlchemy** — for robust, async-capable ORM support.
- **ruff** and **black** — for keeping the codebase clean with zero friction.
- **ACFE (Association of Certified Fraud Examiners)** — for the 2026 fraud statistics that motivated this project.
