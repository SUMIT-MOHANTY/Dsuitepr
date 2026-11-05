# Flask React Todo App - Architecture Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Component Architecture](#component-architecture)
4. [Security Architecture](#security-architecture)
5. [Deployment Patterns](#deployment-patterns)
6. [Environment Configuration](#environment-configuration)
7. [Troubleshooting Runbooks](#troubleshooting-runbooks)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Layer                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │   Web Browser   │  │   Mobile App    │  │   API Clients   │            │
│  │   (React SPA)   │  │   (Future)      │  │   (curl, etc)   │            │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
└───────────┼────────────────────┼────────────────────┼───────────────────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
┌────────────────────────────────┼──────────────────────────────────────────┐
│                         Reverse Proxy Layer                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Nginx (80/443)                              │    │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐  │    │
│  │  │  Static     │    │   API       │    │   SSL/TLS Termination   │  │    │
│  │  │  Files      │    │   Proxy     │    │   Rate Limiting         │  │    │
│  │  │  (React)    │    │   (/api/*)  │    │   Security Headers      │  │    │
│  │  └─────────────┘    └──────┬──────┘    └─────────────────────────┘  │    │
│  └─────────────────────────────┼───────────────────────────────────────┘    │
└────────────────────────────────┼──────────────────────────────────────────────┘
                                 │
┌────────────────────────────────┼──────────────────────────────────────────────┐
│                         Application Layer                                    │
│  ┌─────────────────────────────┼───────────────────────────────────────┐      │
│  │                    Flask Backend (Port 5000)                         │      │
│  │  ┌────────────────────────────┼─────────────────────────────────┐   │      │
│  │  │                    Flask-RESTX API                            │   │      │
│  │  │  ┌──────────┐  ┌──────────┼──────────┐  ┌──────────────┐  │   │      │
│  │  │  │  Auth    │  │  Todos   │          │  │   Users      │  │   │      │
│  │  │  │  Module  │  │  Module  │          │  │   Module     │  │   │      │
│  │  │  └────┬─────┘  └────┬─────┘          │  └──────┬───────┘  │   │      │
│  │  │       │             │                │         │          │   │      │
│  │  │  ┌────┴─────────────┴────────────────┴─────────┴────────┐ │   │      │
│  │  │  │              Service Layer                           │ │   │      │
│  │  │  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │ │   │      │
│  │  │  │  │   Auth      │  │   Todo      │  │   User       │  │ │   │      │
│  │  │  │  │   Service   │  │   Service   │  │   Service    │  │ │   │      │
│  │  │  │  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘  │ │   │      │
│  │  │  └─────────┼────────────────┼────────────────┼──────────┘ │   │      │
│  │  └────────────┼────────────────┼────────────────┼────────────┘   │      │
│  └───────────────┼────────────────┼────────────────┼────────────────┘      │
└──────────────────┼────────────────┼────────────────┼───────────────────────┘
                   │                │                │
┌──────────────────┼────────────────┼────────────────┼───────────────────────┐
│                  │         Data Layer                                   │
│  ┌───────────────┼────────────────┼────────────────┼─────────────────┐      │
│  │               │                │                │                 │      │
│  │  ┌────────────┴───┐  ┌─────────┴────────┐  ┌───┴────────────────┐ │      │
│  │  │   PostgreSQL   │  │     Redis        │  │   File System      │ │      │
│  │  │   (Primary DB) │  │   (Cache/Rate)   │  │   (Static Assets)  │ │      │
│  │  └────────────────┘  └──────────────────┘  └────────────────────┘ │      │
│  └──────────────────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React 18 + TypeScript | SPA UI framework |
| Frontend | Vite | Build tool and dev server |
| Frontend | Tailwind CSS | Utility-first CSS framework |
| Frontend | Zustand | State management |
| Frontend | React Query | Server state management |
| Frontend | React Hook Form | Form handling |
| Frontend | Zod | Schema validation |
| Backend | Flask + Flask-RESTX | REST API framework |
| Backend | SQLAlchemy | ORM for database operations |
| Backend | Flask-JWT-Extended | JWT authentication |
| Backend | Flask-Limiter | Rate limiting |
| Backend | Gunicorn | WSGI HTTP server |
| Database | PostgreSQL 15 | Primary data store |
| Cache | Redis 7 | Caching and rate limiting |
| Proxy | Nginx 1.25 | Reverse proxy and static file server |
| Container | Docker + Docker Compose | Containerization and orchestration |

---

## Architecture Patterns

### Clean Architecture Pattern

The backend follows the **Clean Architecture** pattern with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│  ┌─────────────────────────────────┐    │
│  │  API Controllers (Flask-RESTX)  │    │
│  │  - Request/Response handling    │    │
│  │  - Input validation               │    │
│  │  - HTTP status codes              │    │
│  └─────────────────────────────────┘    │
├─────────────────────────────────────────┤
│           Service Layer                 │
│  ┌─────────────────────────────────┐    │
│  │  Business Logic Services      │    │
│  │  - Authentication logic         │    │
│  │  - Todo operations              │    │
│  │  - User management              │    │
│  └─────────────────────────────────┘    │
├─────────────────────────────────────────┤
│           Data Access Layer             │
│  ┌─────────────────────────────────┐    │
│  │  Repository / Models (SQLAlchemy)│   │
│  │  - Database queries               │    │
│  │  - Entity definitions             │    │
│  │  - Relationships                  │    │
│  └─────────────────────────────────┘    │
├─────────────────────────────────────────┤
│           Infrastructure Layer          │
│  ┌─────────────────────────────────┐    │
│  │  External Services              │    │
│  │  - Database connections           │    │
│  │  - Cache (Redis)                  │    │
│  │  - Email/Notifications            │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**Dependency Rule**: Dependencies point inward. The inner layers (Domain) know nothing about the outer layers.

### Frontend Architecture Pattern

The React frontend follows a **Feature-Based Folder Structure** with clear separation:

```
src/
├── components/          # Reusable UI components
│   ├── common/         # Shared components (Button, Input, Modal)
│   ├── layout/         # Layout components (Header, Sidebar)
│   └── todos/          # Feature-specific components
├── pages/              # Route-level page components
├── services/           # API service layer
├── stores/             # State management (Zustand)
├── hooks/              # Custom React hooks
├── types/              # TypeScript type definitions
├── utils/              # Utility functions and constants
└── providers/          # Context providers
```

---

## Component Architecture

### Backend Components

#### API Layer (`backend/app/api/`)

| Component | Responsibility |
|-----------|----------------|
| `auth.py` | Authentication endpoints (register, login, logout, token refresh) |
| `todos.py` | Todo CRUD operations, filtering, pagination, bulk operations |
| `users.py` | User profile management |
| `__init__.py` | Blueprint registration and API namespace setup |

#### Service Layer (`backend/app/services/`)

| Service | Responsibility |
|---------|----------------|
| `auth_service.py` | JWT token generation, password hashing, session management |
| `todo_service.py` | Business logic for todos, filtering, sorting |
| `user_service.py` | User CRUD, profile updates |

#### Data Layer (`backend/app/models/`)

| Model | Description |
|-------|-------------|
| `User` | User accounts with password hashing |
| `Todo` | Todo items with priorities, status, relationships |

#### Schema Layer (`backend/app/schemas/`)

| Schema | Purpose |
|--------|---------|
| `UserCreate`, `UserLogin`, `UserResponse` | User serialization/deserialization |
| `TodoCreate`, `TodoUpdate`, `TodoResponse` | Todo serialization/deserialization |

### Frontend Components

#### Component Hierarchy

```
App
├── QueryProvider (React Query)
├── AuthGuard (Authentication wrapper)
└── AppLayout
    ├── Header
    │   ├── Logo
    │   ├── Navigation
    │   └── UserMenu
    ├── Sidebar
    │   └── NavigationLinks
    └── MainContent
        ├── Routes
        │   ├── /login → LoginPage
        │   ├── /register → RegisterPage
        │   ├── /dashboard → DashboardPage
        │   ├── /profile → ProfilePage
        │   └── * → NotFoundPage
        └── Modals (global)
```

#### State Management

**Zustand Stores:**

| Store | State | Actions |
|-------|-------|-----------|
| `authStore` | user, isAuthenticated, isLoading | login, register, logout, updateProfile |
| `uiStore` | sidebarOpen, theme, notifications | toggleSidebar, setTheme, addNotification |

**React Query:**

| Query Key | Purpose |
|-----------|---------|
| `['todos']` | Fetch all todos |
| `['todos', filter]` | Fetch filtered todos |
| `['todos', id]` | Fetch single todo |
| `['user', 'profile']` | Fetch user profile |

---

## Security Architecture

### Authentication Flow

```
┌──────────┐                    ┌──────────┐                    ┌──────────┐
│  Client  │                    │  Flask   │                    │  PostgreSQL│
└────┬─────┘                    └────┬─────┘                    └────┬─────┘
     │                             │                               │
     │  POST /api/auth/register    │                               │
     │  {email, password}          │                               │
     │────────────────────────────>│                               │
     │                             │                               │
     │                             │  Hash password (bcrypt)       │
     │                             │  Create user record             │
     │                             │──────────────────────────────>│
     │                             │                               │
     │                             │  Return user (no password)    │
     │                             │<──────────────────────────────│
     │                             │                               │
     │  201 Created                │                               │
     │  {user, message}            │                               │
     │<────────────────────────────│                               │
     │                             │                               │
     │  POST /api/auth/login       │                               │
     │  {email, password}          │                               │
     │────────────────────────────>│                               │
     │                             │                               │
     │                             │  Verify password              │
     │                             │  Generate JWT tokens          │
     │                             │                               │
     │  200 OK                     │                               │
     │  {access_token, refresh_token, user}                        │
     │<────────────────────────────│                               │
     │                             │                               │
     │  GET /api/todos             │                               │
     │  Authorization: Bearer ...  │                               │
     │────────────────────────────>│                               │
     │                             │  Validate JWT                 │
     │                             │  Load user from token           │
     │                             │                               │
     │  200 OK                     │                               │
     │  {todos: [...]}             │                               │
     │<────────────────────────────│                               │
```

### JWT Token Strategy

| Token Type | Expiration | Storage | Usage |
|------------|------------|---------|-------|
| Access Token | 15 minutes | Memory (Zustand) | API authentication |
| Refresh Token | 7 days | HTTP-only cookie | Token refresh |

### Security Headers

Nginx configuration includes security headers:

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; ..." always;
```

### CORS Configuration

```python
# Flask CORS settings
CORS_ORIGINS = [
    "https://yourdomain.com",
    "https://app.yourdomain.com"
]

CORS_SUPPORTS_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = ["Content-Type", "Authorization", "X-Requested-With"]
```

### Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/auth/login` | 5 requests | 1 minute |
| `/api/auth/register` | 3 requests | 1 minute |
| `/api/*` (authenticated) | 100 requests | 1 minute |
| `/api/*` (anonymous) | 30 requests | 1 minute |

**Storage Backends:**
- Development: In-memory
- Production: Redis

### Password Security

- **Hashing Algorithm**: bcrypt with salt rounds 12
- **Minimum Length**: 8 characters
- **Requirements**: Uppercase, lowercase, number, special character
- **Storage**: Never store plain text; only bcrypt hashes

---

## Deployment Patterns

### Blue-Green Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                        Load Balancer                             │
│                           (Nginx/ALB)                            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
┌─────────────────────────┐      ┌─────────────────────────┐
│      Blue Environment   │      │     Green Environment   │
│  ┌─────────────────┐    │      │  ┌─────────────────┐    │
│  │   Nginx (v1)    │    │      │  │   Nginx (v2)    │    │
│  └────────┬────────┘    │      │  └────────┬────────┘    │
│           │             │      │           │             │
│  ┌────────┴────────┐    │      │  ┌────────┴────────┐    │
│  │  Flask (v1.0)   │    │      │  │  Flask (v1.1)   │    │
│  └─────────────────┘    │      │  └─────────────────┘    │
│                         │      │                         │
│  ┌─────────────────┐    │      │  ┌─────────────────┐    │
│  │  PostgreSQL     │◄───┼──────┼──┤  PostgreSQL     │    │
│  │  (Shared)       │    │      │  │  (Shared)       │    │
│  └─────────────────┘    │      │  └─────────────────┘    │
└─────────────────────────┘      └─────────────────────────┘
         ACTIVE                          IDLE
```

**Deployment Steps:**
1. Deploy new version to Green environment
2. Run health checks on Green
3. Switch load balancer to Green
4. Monitor for errors
5. If issues detected, rollback by switching back to Blue

### Rolling Deployment

```
Time ──────────────────────────────────────────────────────────────>

┌─────────┐
│ Pod 1   │ v1
└─────────┘
     │
     ▼
┌─────────┐
│ Pod 1   │ v2  ┌─────────┐
└─────────┘     │ Pod 2   │ v1
                └─────────┘
                     │
                     ▼
┌─────────┐     ┌─────────┐
│ Pod 1   │ v2  │ Pod 2   │ v2  ┌─────────┐
└─────────┘     └─────────┘     │ Pod 3   │ v1
                                └─────────┘
                                     │
                                     ▼
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Pod 1   │ v2  │ Pod 2   │ v2  │ Pod 3   │ v2
└─────────┘     └─────────┘     └─────────┘
           DEPLOYMENT COMPLETE
```

### Health Check Strategy

| Service | Endpoint | Expected Response |
|---------|----------|-------------------|
| Nginx | `/health` | `200 OK` + "healthy" |
| Flask | `/api/health` | `200 OK` + JSON health status |
| PostgreSQL | `pg_isready` | Exit code 0 |
| Redis | `PING` | `PONG` |

### Database Migration Strategy

**Zero-Downtime Migrations:**

1. **Additive Changes** (new columns, tables):
   - Deploy migration first
   - Deploy application code

2. **Destructive Changes** (column removal, type changes):
   - Deploy code to stop using column
   - Deploy migration to remove column

3. **Data Migrations**:
   - Run in background job
   - Use batch processing for large datasets

---

## Environment Configuration

### Environment Variables Template

```bash
# =============================================================================
# Flask React Todo App - Environment Variables Template
# =============================================================================
# Copy this file to .env and fill in your values
# DO NOT commit .env to version control!
# =============================================================================

# -----------------------------------------------------------------------------
# Application Settings
# -----------------------------------------------------------------------------
APP_NAME=Flask React Todo App
APP_ENV=production
APP_DEBUG=false
APP_PORT=5000

# -----------------------------------------------------------------------------
# Security Settings
# -----------------------------------------------------------------------------
# Generate with: openssl rand -hex 32
SECRET_KEY=your-super-secret-key-here-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-here-min-32-chars

# JWT Configuration
JWT_ACCESS_TOKEN_EXPIRES=900
JWT_REFRESH_TOKEN_EXPIRES=604800

# -----------------------------------------------------------------------------
# Database Settings
# -----------------------------------------------------------------------------
DB_HOST=localhost
DB_PORT=5432
DB_NAME=todoapp
DB_USER=todoapp
DB_PASSWORD=your-secure-db-password

# Full database URL (alternative to individual settings)
# Format: postgresql://user:password@host:port/database
DATABASE_URL=postgresql://todoapp:password@localhost:5432/todoapp

# -----------------------------------------------------------------------------
# Redis Settings (Optional - for caching and rate limiting)
# -----------------------------------------------------------------------------
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Rate limiting storage URL
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/0

# -----------------------------------------------------------------------------
# CORS Settings
# -----------------------------------------------------------------------------
# Comma-separated list of allowed origins
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# -----------------------------------------------------------------------------
# Email Settings (Optional - for notifications)
# -----------------------------------------------------------------------------
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TLS=true

# -----------------------------------------------------------------------------
# Logging Settings
# -----------------------------------------------------------------------------
LOG_LEVEL=INFO
LOG_FORMAT=json

# -----------------------------------------------------------------------------
# Frontend Settings
# -----------------------------------------------------------------------------
VITE_API_URL=https://yourdomain.com/api
VITE_APP_NAME=Flask React Todo App

# -----------------------------------------------------------------------------
# Platform-Specific Settings
# -----------------------------------------------------------------------------

# AWS ECS
AWS_REGION=us-east-1
ECS_CLUSTER_NAME=todo-app-cluster
ECS_SERVICE_NAME=todo-app-service

# GCP Cloud Run
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1

# Azure Container Apps
AZURE_RESOURCE_GROUP=todo-app-rg
AZURE_CONTAINER_APP_NAME=todo-app

# Heroku
HEROKU_APP_NAME=your-app-name
HEROKU_API_KEY=your-api-key

# Railway
RAILWAY_PROJECT_ID=your-project-id
RAILWAY_ENVIRONMENT=production
```

### Environment-Specific Configurations

| Environment | Debug | Rate Limit | CORS Origins | Logging |
|-------------|-------|------------|--------------|---------|
| Development | True | Disabled | `*` | DEBUG |
| Staging | False | 100/min | Staging domain | INFO |
| Production | False | 100/min | Production domain | WARNING |

---

## Troubleshooting Runbooks

### Runbook 1: Application Won't Start

**Symptoms:**
- Container exits immediately
- `docker-compose ps` shows Exit code
- Logs show error on startup

**Diagnostic Steps:**

1. Check container logs:
   ```bash
   docker-compose logs backend
   docker-compose logs nginx
   ```

2. Verify environment variables:
   ```bash
   docker-compose exec backend env | grep -E '(SECRET_KEY|DATABASE_URL)'
   ```

3. Check database connectivity:
   ```bash
   docker-compose exec backend python -c "
   import psycopg2
   conn = psycopg2.connect('$DATABASE_URL')
   print('Database connection successful')
   conn.close()
   "
   ```

**Common Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| Missing SECRET_KEY | Generate with `openssl rand -hex 32` |
| Invalid DATABASE_URL | Check format: `postgresql://user:pass@host:port/db` |
| Database not ready | Add `depends_on` with health check |
| Port conflict | Change port mapping in docker-compose.yml |
| Permission denied | Check file permissions on volumes |

---

### Runbook 2: Database Connection Failures

**Symptoms:**
- 500 errors on API calls
- "Connection refused" in logs
- "FATAL: password authentication failed"

**Diagnostic Steps:**

1. Check database container status:
   ```bash
   docker-compose ps db
   docker-compose logs db
   ```

2. Test database connection:
   ```bash
   docker-compose exec db pg_isready -U $DB_USER
   ```

3. Verify credentials:
   ```bash
   # Check environment variables match
   docker-compose exec backend printenv | grep DB_
   docker-compose exec db printenv | grep POSTGRES
   ```

**Common Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| Database not started | `docker-compose up -d db` |
| Wrong password | Reset with `docker-compose exec db psql -U postgres -c "ALTER USER $DB_USER WITH PASSWORD 'newpassword';"` |
| Database doesn't exist | Create with `docker-compose exec db createdb -U $DB_USER $DB_NAME` |
| Network issues | Restart with `docker-compose down && docker-compose up -d` |

---

### Runbook 3: 502 Bad Gateway from Nginx

**Symptoms:**
- Browser shows "502 Bad Gateway"
- Nginx error logs show "connect() failed"

**Diagnostic Steps:**

1. Check backend health:
   ```bash
   docker-compose exec backend python -c "
   import urllib.request
   response = urllib.request.urlopen('http://localhost:5000/api/health')
   print(response.read().decode())
   "
   ```

2. Verify Nginx upstream configuration:
   ```bash
   docker-compose exec nginx nginx -t
   ```

3. Check network connectivity:
   ```bash
   docker-compose exec nginx wget -O- http://backend:5000/api/health
   ```

**Common Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| Backend not running | `docker-compose up -d backend` |
| Wrong upstream name | Verify `proxy_pass http://backend:5000` in nginx.conf |
| Backend crashed | Check logs: `docker-compose logs --tail=100 backend` |
| Network not connected | `docker-compose down && docker-compose up -d` |

---

### Runbook 4: Static Assets Not Loading

**Symptoms:**
- 404 errors for CSS/JS files
- Page loads without styling
- Console shows "Failed to load resource"

**Diagnostic Steps:**

1. Check Nginx static file location:
   ```bash
   docker-compose exec nginx ls -la /usr/share/nginx/html/
   ```

2. Verify volume mounts:
   ```bash
   docker-compose config | grep -A5 volumes
   ```

3. Check frontend build:
   ```bash
   docker-compose run --rm frontend-builder ls -la /app/dist/
   ```

**Common Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| Frontend not built | Run `docker-compose --profile build up frontend-builder` |
| Wrong root path | Verify `root /usr/share/nginx/html` in nginx.conf |
| Volume not mounted | Check docker-compose.yml volume definitions |
| Build output missing | Verify `dist` folder exists in frontend |

---

### Runbook 5: JWT Authentication Failures

**Symptoms:**
- 401 Unauthorized errors
- "Invalid token" messages
- Login works but subsequent requests fail

**Diagnostic Steps:**

1. Check token format:
   ```bash
   # Decode JWT header (first part before first dot)
   echo "eyJ0eXAiOiJKV1Qi..." | base64 -d
   ```

2. Verify SECRET_KEY consistency:
   ```bash
   docker-compose exec backend python -c "
   from app.config import Config
   print(f'SECRET_KEY length: {len(Config.SECRET_KEY)}')
   "
   ```

3. Check token expiration:
   ```bash
   # Decode payload (second part)
   echo "eyJzdWIiOiIxMjM0NTY3..." | base64 -d
   # Check "exp" field
   ```

**Common Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| Token expired | Re-login to get fresh token |
| Wrong SECRET_KEY | Ensure same key across all backend instances |
| Clock skew | Sync server time with NTP |
| Token not sent | Verify `Authorization: Bearer <token>` header |

---

### Runbook 6: Rate Limiting Blocking Requests

**Symptoms:**
- 429 Too Many Requests errors
- Requests blocked after few attempts

**Diagnostic Steps:**

1. Check rate limit headers:
   ```bash
   curl -I https://yourdomain.com/api/todos
   # Look for X-RateLimit-* headers
   ```

2. Verify Redis connection (if using Redis):
   ```bash
   docker-compose exec redis redis-cli ping
   ```

3. Check rate limit configuration:
   ```bash
   docker-compose exec backend python -c "
   from flask_limiter import Limiter
   print(limiter.current_limits)
   "
   ```

**Common Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| Legitimate high traffic | Increase rate limits or implement caching |
| Redis not available | Start Redis or switch to in-memory storage |
| Configuration too strict | Adjust limits in config.py |
| Shared IP issue | Use authenticated rate limiting instead of IP-based |

---

### Runbook 7: SSL/HTTPS Issues

**Symptoms:**
- "Your connection is not private" in browser
- Certificate errors
- HTTPS redirects not working

**Diagnostic Steps:**

1. Check certificate validity:
   ```bash
   openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
   ```

2. Verify certificate files:
   ```bash
   docker-compose exec nginx ls -la /etc/nginx/ssl/
   ```

3. Check Certbot logs:
   ```bash
   docker-compose logs certbot
   ```

**Common Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| Certificate expired | Renew with `docker-compose run --rm certbot renew` |
| Wrong certificate path | Update nginx.conf with correct paths |
| Domain mismatch | Ensure certificate covers your domain |
| Mixed content | Update all URLs to use HTTPS |

---

### Runbook 8: High Memory Usage

**Symptoms:**
- Container OOM killed
- System running out of memory
- Slow response times

**Diagnostic Steps:**

1. Check container memory usage:
   ```bash
   docker stats --no-stream
   ```

2. Check for memory leaks:
   ```bash
   docker-compose exec backend python -c "
   import gc
   print(f'Garbage collector counts: {gc.get_count()}')
   print(f'Garbage thresholds: {gc.get_threshold()}')
   "
   ```

3. Monitor database connections:
   ```bash
   docker-compose exec db psql -U $DB_USER -c "SELECT count(*) FROM pg_stat_activity;"
   ```

**Common Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| Memory leak in app | Profile with memory_profiler, fix leaks |
| Too many workers | Reduce Gunicorn workers in Dockerfile |
| Database connection pool | Limit SQLAlchemy pool size |
| No resource limits | Add memory limits in docker-compose.yml |

---

### Runbook 9: CI/CD Pipeline Failures

**Symptoms:**
- GitHub Actions workflow fails
- Build or test step errors
- Deployment rejected

**Diagnostic Steps:**

1. Check workflow logs in GitHub Actions UI

2. Verify secrets are configured:
   ```bash
   # In GitHub repository settings
   Settings > Secrets and variables > Actions
   ```

3. Test locally:
   ```bash
   # Run same commands as CI
   cd backend && pip install -r requirements.txt && pytest
   cd frontend && npm ci && npm run build
   ```

**Common Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| Missing secrets | Add required secrets to GitHub repository |
| Test failures | Fix failing tests locally first |
| Dependency issues | Update lock files (requirements.txt, package-lock.json) |
| Docker build fails | Test build locally: `docker build .` |
| Coverage below threshold | Add tests to reach 80% coverage |

---

### Runbook 10: Database Migration Failures

**Symptoms:**
- Migration fails to apply
- "Table already exists" errors
- Schema mismatch errors

**Diagnostic Steps:**

1. Check migration status:
   ```bash
   docker-compose exec backend flask db current
   docker-compose exec backend flask db history
   ```

2. View migration details:
   ```bash
   docker-compose exec backend flask db show <revision>
   ```

3. Check database schema:
   ```bash
   docker-compose exec db psql -U $DB_USER -d $DB_NAME -c "\dt"
   ```

**Common Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| Migration already applied | Mark as done: `flask db stamp <revision>` |
| Conflicting migration | Merge or manually resolve conflicts |
| Data incompatible | Add data migration script |
| Missing table | Create manually or fix migration |

---

## Quick Reference Commands

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Restart service
docker-compose restart backend

# Rebuild and start
docker-compose up -d --build

# Stop all
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Database

```bash
# Connect to database
docker-compose exec db psql -U $DB_USER -d $DB_NAME

# Run migrations
docker-compose exec backend flask db upgrade

# Create migration
docker-compose exec backend flask db migrate -m "description"

# Backup database
docker-compose exec db pg_dump -U $DB_USER $DB_NAME > backup.sql

# Restore database
docker-compose exec -T db psql -U $DB_USER $DB_NAME < backup.sql
```

### Health Checks

```bash
# Check all services
docker-compose ps

# Check backend health
curl http://localhost:5000/api/health

# Check Nginx health
curl http://localhost/health

# Check database
docker-compose exec db pg_isready -U $DB_USER
```

---

## Support and Resources

- **Documentation**: See `docs/DEPLOYMENT.md` for platform-specific guides
- **Issues**: Check GitHub Issues for known problems
- **Logs**: Always check `docker-compose logs` first when troubleshooting
- **Monitoring**: Set up health checks and alerts for production deployments
