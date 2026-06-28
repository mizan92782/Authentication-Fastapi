ok # FastAPI Gmail Authentication Template

A production-ready FastAPI authentication template with OTP-based registration via Gmail SMTP, JWT tokens, Redis caching, Celery async email, and RabbitMQ message broker.

---

## Features

- OTP-based user registration (6-digit, expires in 5 minutes)
- Gmail SMTP email delivery via Celery background tasks
- JWT access + refresh token authentication
- Token blacklisting on logout
- Password reset via OTP
- Brute-force protection (lockout after 3 failed OTP attempts)
- Rate limiting per IP (stored in Redis, works across multiple workers)
- OTP resend cooldown (60 seconds)
- Soft delete pattern
- Async PostgreSQL via Tortoise ORM
- Structured logging with structlog

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| Database | PostgreSQL + Tortoise ORM |
| Cache / Rate limit | Redis |
| Task Queue | Celery + RabbitMQ |
| Email | Gmail SMTP |
| Auth | JWT (python-jose) |
| Password | bcrypt |
| Containerization | Docker + Docker Compose |

---

## Project Structure

```
fastry/
├── app/
│   ├── api/v1/              # Route handlers (thin layer, no business logic)
│   │   └── auth_routes.py
│   ├── core/                # Config, security, DB, logging, limiter
│   ├── infrastructure/
│   │   ├── celery/          # Celery app + tasks
│   │   ├── email/           # SMTP mailer
│   │   └── redis/           # Cache clients
│   ├── middleware/          # Request logging, exception handler
│   ├── modules/
│   │   ├── auth/            # Auth service + schemas
│   │   └── users/           # User model, repository, schemas
│   └── shared/              # Base model, enums, utils, responses
├── main.py
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Authentication Flow

```
1. POST /auth/user/register/       → validates data, sends OTP to Gmail
2. POST /auth/user/otp-verify/     → verifies OTP, creates user, returns tokens
3. POST /auth/user/login/          → email + password → returns tokens
4. POST /auth/user/token-refresh/  → refresh token → new access token
5. POST /auth/user/logout/         → blacklists refresh token
```

```
Password Reset Flow:
1. POST /auth/user/password-reset/  → sends OTP to Gmail
2. POST /auth/user/password-change/ → verifies OTP, updates password
```

---

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url>
cd fastry
cp .env.example .env
```

### 2. Configure Gmail SMTP in `.env`

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password       # Gmail App Password, not account password
SMTP_FROM=noreply@yourdomain.com
```

> **How to get Gmail App Password:**
> Google Account → Security → 2-Step Verification → App Passwords → Generate

### 3. Set required environment variables

```env
APP_SECRET_KEY=your-very-long-random-secret-key

DB_HOST=postgres
DB_USER=ecommerce_user
DB_PASSWORD=ecommerce_password
DB_NAME=ecommerce_db

REDIS_HOST=redis
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
```

### 4. Run with Docker

```bash
docker compose up --build -d
```

### 5. Access

| Service | URL |
|---------|-----|
| API Docs (Swagger) | http://localhost:8001/docs |
| pgAdmin | http://localhost:5051 |
| RabbitMQ Management | http://localhost:15674 |

---

## API Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/auth/user/register/` | Register — sends OTP | 5/min |
| POST | `/auth/user/otp-verify/` | Verify OTP — returns tokens | 10/min |
| POST | `/auth/user/otp-resend/` | Resend OTP (60s cooldown) | 3/min |
| POST | `/auth/user/login/` | Login | 10/min |
| POST | `/auth/user/token-refresh/` | Refresh access token | — |
| POST | `/auth/user/logout/` | Logout — blacklists token | — |
| POST | `/auth/user/password-reset/` | Request password reset OTP | 5/min |
| POST | `/auth/user/password-change/` | Change password via OTP | 5/min |

---

## Security

- OTP is 6 digits, expires in 5 minutes
- Max 3 wrong OTP attempts before session lockout
- 60-second cooldown between OTP resends
- Rate limits stored in Redis (works across multiple workers/containers)
- Password reset response never reveals if email exists (prevents enumeration)
- Refresh tokens blacklisted on logout and password change
- Passwords hashed with bcrypt

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_SECRET_KEY` | JWT signing secret | — |
| `APP_ENV` | `development` or `production` | `development` |
| `DB_HOST` | PostgreSQL host | `postgres` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_USER` | PostgreSQL user | — |
| `DB_PASSWORD` | PostgreSQL password | — |
| `DB_NAME` | PostgreSQL database | — |
| `REDIS_HOST` | Redis host | `redis` |
| `REDIS_PORT` | Redis port | `6379` |
| `RABBITMQ_HOST` | RabbitMQ host | `rabbitmq` |
| `RABBITMQ_USER` | RabbitMQ user | `guest` |
| `RABBITMQ_PASSWORD` | RabbitMQ password | `guest` |
| `SMTP_HOST` | SMTP host | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | Gmail address | — |
| `SMTP_PASSWORD` | Gmail app password | — |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `30` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |
| `RATE_LIMIT_PER_MINUTE` | Global rate limit | `60` |

---

## License

MIT
