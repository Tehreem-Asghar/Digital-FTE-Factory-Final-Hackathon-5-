# SaaSFlow Digital FTE Factory

> **Multi-channel AI-powered Customer Success Agent System**

A production-ready CRM and ticket management system that processes customer support requests across multiple channels (Web Form, Email, WhatsApp) using AI agents. Built for the CRM Digital FTE Factory Hackathon 5.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135+-green.svg)
![Next.js](https://img.shields.io/badge/Next.js-16-black.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)
![Kafka](https://img.shields.io/badge/Apache_Kafka-7.5.0-red.svg)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Detailed Setup](#-detailed-setup)
- [Running Components](#-running-components)
- [API Documentation](#-api-documentation)
- [Dashboard](#-dashboard)
- [Testing](#-testing)
- [Environment Variables](#-environment-variables)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### Multi-Channel Support
- **Web Form**: Customer support ticket submission via web interface
- **Email**: Automated email processing via Gmail integration
- **WhatsApp**: Real-time messaging via Meta WhatsApp Cloud API

### AI Agent Capabilities
- **Intelligent Routing**: Automatically categorizes and prioritizes tickets
- **Cross-Channel Identity**: Links customers across email, phone, and WhatsApp
- **Knowledge Base Search**: Semantic search using Gemini embeddings (768-dimensional vectors)
- **Contextual Responses**: Maintains conversation history for coherent responses
- **Escalation Detection**: Identifies when human intervention is needed

### Resilience
- **Fail-Safe Ingestion**: Messages saved to database when Kafka is unavailable
- **Recovery Worker**: Automatically drains pending messages when Kafka recovers
- **Message Retry**: Up to 5 retry attempts with exponential backoff

### Observability
- **Health Endpoints**: Real-time system health monitoring
- **Metrics Dashboard**: Per-channel latency, escalation rates, throughput
- **Structured Logging**: JSON logs for easy aggregation

---

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Web Form  │     │    Email    │     │  WhatsApp   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼──────┐
                    │  FastAPI    │
                    │    API      │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐ ┌───▼────┐ ┌────▼─────┐
       │  PostgreSQL │ │ Kafka  │ │ pgvector │
       │  + pgvector │ │ Queue  │ │ Embeddings│
       └──────┬──────┘ └───┬────┘ └──────────┘
              │            │
       ┌──────▼──────┐ ┌───▼────────┐
       │   Worker    │ │  Recovery  │
       │  (Consumer) │ │   Worker   │
       └─────────────┘ └────────────┘
```

### Components

| Component | Technology | Port | Description |
|-----------|-----------|------|-------------|
| **API** | FastAPI (Python 3.11) | 8000 | REST endpoints for all channels |
| **Worker** | Kafka Consumer | - | Processes messages, runs AI agent |
| **Dashboard** | Next.js 16 | 3000 | Admin UI for tickets & analytics |
| **Database** | PostgreSQL + pgvector | 5433 | Customers, tickets, knowledge base |
| **Message Queue** | Apache Kafka | 9092 | Async event bus |
| **Recovery Worker** | Python async | - | Drains pending_ingestion on recovery |

---

## 🛠️ Tech Stack

### Backend
- **Runtime**: Python 3.11+
- **Framework**: FastAPI 0.135+
- **Package Manager**: uv
- **Async**: asyncio, asyncpg
- **AI**: OpenAI Agents SDK, Gemini (embeddings)

### Frontend
- **Framework**: Next.js 16
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4
- **Charts**: Recharts

### Infrastructure
- **Database**: PostgreSQL with pgvector extension
- **Message Queue**: Apache Kafka 7.5.0
- **Containerization**: Docker, Docker Compose

### Testing
- **Unit/Integration**: pytest, pytest-asyncio
- **Load Testing**: Locust
- **Chaos Testing**: Custom chaos_sim.py

---

## 📦 Prerequisites

| Requirement | Version | Installation |
|-------------|---------|--------------|
| **Python** | 3.11+ | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) |
| **Docker** | 20+ | [docker.com](https://www.docker.com/get-started/) |
| **uv** | Latest | See below |
| **Git** | Latest | [git-scm.com](https://git-scm.com/) |

### Install uv (Python Package Manager)

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd "CRM Digital FTE Factory Hackathon 5\Hackathon_5"

# 2. Install Python dependencies
uv sync

# 3. Create .env file (see Environment Variables section)
copy .env.example .env
# Edit .env with your API keys

# 4. Start infrastructure (PostgreSQL, Kafka, Zookeeper)
docker-compose up -d

# 5. Seed the knowledge base
uv run python seed_kb.py

# 6. Start the API server
uv run uvicorn production.api.main:app --host 0.0.0.0 --port 8000

# 7. Start the message worker (new terminal)
uv run python -m production.workers.message_processor

# 8. Start the dashboard (new terminal)
cd dashboard
npm install
npm run dev
```

**Access Points:**
- **API**: http://localhost:8000
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

---

## 📖 Detailed Setup

### Step 1: Environment Configuration

Create a `.env` file in the project root:

```bash
# ==================== DATABASE ====================
POSTGRES_USER=fte_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=fte_db

# ==================== AI SERVICES ====================
OPENAI_API_KEY=sk-your-openai-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here

# ==================== KAFKA ====================
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_TICKETS=fte.tickets.incoming
KAFKA_TOPIC_RESPONSES=fte.tickets.responses
KAFKA_CONSUMER_GROUP=fte-message-processor

# ==================== EMAIL (SMTP) ====================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_USE_TLS=true

# ==================== WHATSAPP (META) ====================
WHATSAPP_TOKEN=your-whatsapp-cloud-api-token
WHATSAPP_PHONE_ID=your-whatsapp-phone-id
WHATSAPP_VERIFY_TOKEN=your-verify-token
WHATSAPP_WEBHOOK_URL=http://localhost:8000/webhooks/whatsapp

# ==================== SERVER ====================
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
```

### Step 2: Database Setup

```bash
# Start PostgreSQL with pgvector
docker-compose up -d db

# Wait for database to be ready (30 seconds)
docker-compose ps

# Verify database connection
docker exec -it hackathon_5-db-1 psql -U fte_user -d fte_db -c "SELECT 1;"

# Seed knowledge base with embeddings
uv run python seed_kb.py
```

### Step 3: Dashboard Setup

```bash
cd dashboard

# Install Node.js dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
npm start
```

---

## ▶️ Running Components

### Start All Infrastructure

```bash
# Start PostgreSQL, Kafka, Zookeeper
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all
docker-compose down
```

### API Server

```bash
# Development mode
uv run uvicorn production.api.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uv run uvicorn production.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Message Worker

```bash
# Start worker (consumes from Kafka)
uv run python -m production.workers.message_processor

# Multiple workers for scaling
uv run python -m production.workers.message_processor &
uv run python -m production.workers.message_processor &
```

### Recovery Worker

```bash
# Drain pending_ingestion table (run when Kafka recovers)
uv run python -m production.workers.recovery_worker --interval 15
```

### Dashboard

```bash
cd dashboard

# Development
npm run dev

# Production
npm run build
npm start
```

---

## 📡 API Documentation

### Interactive API Docs

Once the API server is running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Intake Channels

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/support/submit` | Web form ticket submission |
| `POST` | `/support/email` | Email support request |
| `POST` | `/support/whatsapp` | WhatsApp message (testing) |
| `POST` | `/webhooks/gmail` | Gmail Pub/Sub webhook |
| `GET/POST` | `/webhooks/whatsapp` | Meta WhatsApp webhook |

#### Dashboard APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/dashboard/stats` | KPIs, charts, recent tickets |
| `GET` | `/api/tickets` | All tickets list |
| `GET` | `/api/tickets/{id}` | Ticket details + messages |
| `GET` | `/api/customers` | All customers list |
| `GET` | `/api/customers/{id}` | Customer details + tickets |

#### Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health check |
| `GET` | `/metrics/channels` | Per-channel metrics |
| `GET` | `/metrics/summary` | Overall metrics summary |
| `GET` | `/customers/lookup` | Customer lookup by email/phone |

### Example: Submit a Ticket

```bash
curl -X POST http://localhost:8000/support/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "subject": "Cannot login",
    "message": "I forgot my password and need help resetting it."
  }'
```

### Example: Check Ticket Status

```bash
curl http://localhost:8000/support/ticket/<ticket-id>
```

---

## 📊 Dashboard

The Next.js dashboard provides:

- **Overview**: KPIs (tickets today, avg response time, escalation rate)
- **Tickets**: View, filter, and manage all tickets
- **Customers**: Customer profiles with conversation history
- **Analytics**: Charts for channel distribution, response times, categories

**Access**: http://localhost:3000

---

## 🧪 Testing

### Run All Tests

```bash
# Full test suite (Stage 2 + Stage 3 E2E)
uv run pytest production/tests/test_production.py tests/test_multichannel_e2e.py -v

# Stage 2 only (49 tests)
uv run pytest production/tests/test_production.py -v

# Stage 3 E2E only (16 tests)
uv run pytest tests/test_multichannel_e2e.py -v

# With coverage
uv run pytest --cov=production --cov-report=html
```

### Load Testing

```bash
# Quick validation (30 users, 60s)
uv run locust -f tests/load_test.py \
  --host http://localhost:8000 \
  --users 30 \
  --spawn-rate 5 \
  --run-time 60s \
  --headless

# Full stress test (150 users, 5 minutes)
uv run locust -f tests/load_test.py \
  --host http://localhost:8000 \
  --users 150 \
  --spawn-rate 10 \
  --run-time 300s \
  --headless
```

**Success Criteria**: P95 latency < 3 seconds (SC-002)

### Chaos Testing

```bash
# Dry-run (no actual kills)
uv run python tests/chaos_sim.py --dry-run --duration 1 --interval 10

# Full 24-hour chaos test
uv run python tests/chaos_sim.py --duration 24 --interval 120
```

**Success Criteria**: >99.9% uptime, zero message loss (SC-003)

### Manual Fail-Safe Test

```bash
# 1. Stop Kafka
docker-compose stop kafka

# 2. Submit a ticket (should save to pending_ingestion)
curl -X POST http://localhost:8000/support/submit \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@test.com","subject":"Test","message":"Testing fail-safe"}'

# 3. Check pending_ingestion table
docker exec hackathon_5-db-1 psql -U fte_user -d fte_db \
  -c "SELECT id, status, payload->>'channel' as channel FROM pending_ingestion;"

# 4. Restart Kafka
docker-compose start kafka

# 5. Run recovery worker
uv run python -m production.workers.recovery_worker --interval 5

# 6. Verify messages are published
docker exec hackathon_5-db-1 psql -U fte_user -d fte_db \
  -c "SELECT id, status, published_at FROM pending_ingestion;"
```

---

## 🔐 Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_USER` | Database username | `fte_user` |
| `POSTGRES_PASSWORD` | Database password | `secure_password` |
| `POSTGRES_DB` | Database name | `fte_db` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `GEMINI_API_KEY` | Google Gemini API key | `...` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker address | `localhost:9092` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_HOST` | SMTP server for email | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `WHATSAPP_TOKEN` | WhatsApp Cloud API token | - |
| `WHATSAPP_PHONE_ID` | WhatsApp phone ID | - |

---

## 📁 Project Structure

```
Hackathon_5/
├── production/                 # Backend code
│   ├── api/                    # FastAPI server
│   │   └── main.py
│   ├── agent/                  # AI agent logic
│   ├── channels/               # Channel implementations
│   ├── database/               # DB schema and utilities
│   │   └── schema.sql
│   ├── workers/                # Kafka consumers
│   │   ├── message_processor.py
│   │   └── recovery_worker.py
│   ├── utils/                  # Shared utilities
│   └── tests/                  # Backend tests
├── dashboard/                  # Next.js frontend
│   ├── app/                    # Next.js app router
│   ├── components/             # React components
│   └── lib/                    # Utilities
├── tests/                      # E2E and load tests
│   ├── test_multichannel_e2e.py
│   ├── load_test.py
│   └── chaos_sim.py
├── context/                    # Project documentation
├── history/                    # Prompt history records
├── docker-compose.yml          # Docker services
├── Dockerfile                  # API container image
├── pyproject.toml              # Python dependencies
├── seed_kb.py                  # Knowledge base seeder
├── RUNBOOK.md                  # Operations runbook
└── README.md                   # This file
```

---

## 👨‍💻 Development

### Code Style

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Strict mode enabled
- **Formatting**: Consistent indentation (4 spaces Python, 2 spaces TS)

### Adding New Features

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes with tests
3. Run test suite: `uv run pytest -v`
4. Commit with descriptive message
5. Create pull request

### Database Migrations

Schema changes are in `production/database/schema.sql`. For migrations:

```bash
# Apply new schema
docker exec -it hackathon_5-db-1 psql -U fte_user -d fte_db -f /docker-entrypoint-initdb.d/schema.sql
```

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Port 5433 in use** | Change port in `docker-compose.yml` or stop other PostgreSQL |
| **Kafka connection refused** | Wait 30s after starting Docker, then restart Kafka |
| **Module not found** | Run `uv sync` |
| **Dashboard build fails** | Ensure Node.js 18+, run `npm cache clean --force` |
| **Embedding generation fails** | Verify `GEMINI_API_KEY` in `.env` |
| **Tests timeout** | Increase timeout in `tests/conftest.py` |

### Debug Commands

```bash
# Check all containers
docker-compose ps

# View logs
docker-compose logs -f kafka
docker-compose logs -f db

# Database connection test
docker exec -it hackathon_5-db-1 psql -U fte_user -d fte_db -c "SELECT 1;"

# Kafka topics
docker exec -it hackathon_5-kafka-1 kafka-topics --bootstrap-server localhost:9092 --list

# Reset everything (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d db
uv run python seed_kb.py
```

### Getting Help

1. Check logs: `docker-compose logs -f`
2. Health endpoint: `curl http://localhost:8000/health`
3. Review `RUNBOOK.md` for operations
4. Check `context/` folder for documentation

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Review Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No hardcoded secrets
- [ ] Error handling implemented
- [ ] Logging added for debugging

---

## 📄 License

This project is part of the CRM Digital FTE Factory Hackathon 5.

---

## 📈 Performance SLA

| Metric | Target | Monitoring |
|--------|--------|-----------|
| Uptime | > 99.9% | `/health` endpoint |
| P95 Latency | < 3 seconds | `agent_metrics` table |
| Escalation Rate | < 25% | `/metrics/channels` |
| Cross-Channel ID | > 95% accuracy | `customer_identifiers` table |
| Message Loss | 0% | `pending_ingestion` status counts |

---

## 🙏 Acknowledgments

- **Hackathon 5**: CRM Digital FTE Factory
- **AI**: OpenAI Agents SDK, Google Gemini
- **Framework**: FastAPI, Next.js
- **Infrastructure**: PostgreSQL, Apache Kafka, Docker

---

**Built with ❤️ for the CRM Digital FTE Factory Hackathon 5**
