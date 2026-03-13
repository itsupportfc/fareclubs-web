# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FareClubs is a full-stack flight booking platform integrating with TBO (Tektravels) for flight search/booking and Razorpay for payments. React+Vite frontend, FastAPI backend, PostgreSQL database.

## Common Commands

### Backend (run from `backend/`)
```bash
pip install -r requirements.txt          # Install dependencies
alembic upgrade head                      # Run database migrations
alembic revision --autogenerate -m "msg"  # Create new migration
uvicorn app.main:app --reload             # Dev server (port 8000)
```

### Frontend (run from `frontend/`)
```bash
npm install        # Install dependencies
npm run dev        # Dev server (Vite)
npm run build      # Production build
npm run lint       # ESLint
```

### Docker (full stack)
```bash
docker-compose up --build   # Starts postgres, redis, backend, nginx on port 80
```

## Architecture

### Provider Abstraction Pattern
The core architectural pattern is a **provider abstraction layer**:
- `schemas/tbo/` — Pydantic models matching TBO's API exactly (PascalCase fields)
- `schemas/internal/` — Provider-agnostic schemas the frontend consumes
- `transformers/tbo_transformer.py` — Converts TBO responses → internal schemas (~1000 lines)
- `clients/tbo_client.py` — HTTP wrapper for TBO API with token caching and async lock

This design allows swapping flight providers without changing the frontend or API contracts.

### Backend Structure
- **API routes** (`app/api/v1/`): `auth.py` (signup/login/JWT), `flight.py` (search/book flow), `airports.py`
- **Services** (`app/services/`): Business logic, e.g. `booking_service.py` handles persistence
- **Dependencies** (`app/api/v1/dependencies.py`): FastAPI `Depends()` for DB sessions, TBO client, transformer, user IP
- **Database**: SQLAlchemy 2.0 async ORM with `asyncpg`, Alembic async migrations
- **Models** (`app/db/models/`): `user.py`, `booking.py` (Booking/Payment/BookingPassenger), `air_data.py` (Airline/Airport)
- **Utils**: `cache.py` (in-memory flight cache, 15min TTL), `razorpay_utils.py`, `email.py` (SMTP staff alerts)

### Frontend Structure
- **State**: Zustand store (`store/useFlightStore.js`) with sessionStorage persistence
- **Routing** (`router/AppRouter.jsx`): `/` home, `/flights/results`, `/return/results`, `/booking/page`, `/one/way/book`, `/booking/confirmation`
- **API client** (`components/api/flight.js`): Axios calls to backend
- **Styling**: Tailwind CSS 4, Framer Motion animations, HeadlessUI, Lucide icons

### Two-Step Booking Flow
1. **Create order**: Frontend calls `/flights/booking/create-order` → backend creates Razorpay order + saves payment record
2. **Confirm booking**: After Razorpay payment, frontend calls `/flights/booking/confirm` → backend verifies signature, calls TBO Book+Ticket, persists booking

### Deployment
- Nginx serves the built frontend SPA and proxies `/api/v1/*` to the backend
- Frontend Dockerfile: multi-stage (Node 22 build → Nginx serve)
- Backend Dockerfile: Python 3.13.7, runs uvicorn

## Key Conventions
- Backend is fully async (async handlers, AsyncSession, httpx async client)
- Global exception handler catches `ExternalProviderError` for TBO failures
- Environment config via Pydantic `BaseSettings` in `app/config.py` (loads from `.env`)
- TBO client auto-authenticates and caches tokens with expiry
