# Quick Start Guide: Digital FTE AI Customer Success Agent

## Overview
This guide provides instructions for setting up and running the Digital FTE AI Customer Success Agent system in a development environment.

## Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend development)
- PostgreSQL 15+ with pgvector extension
- Docker and Docker Compose (for containerized deployment)
- Git

## Backend Setup (FastAPI)

### 1. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your configuration:
# - DATABASE_URL: PostgreSQL connection string
# - OPENAI_API_KEY: Your OpenAI API key
# - KAFKA_BOOTSTRAP_SERVERS: Kafka connection string
# - GMAIL_CREDENTIALS_PATH: Path to Gmail API credentials
# - TWILIO_ACCOUNT_SID: Twilio account SID
# - TWILIO_AUTH_TOKEN: Twilio auth token
# - TWILIO_WHATSAPP_NUMBER: Your Twilio WhatsApp sandbox number
```

### 2. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Database Setup
```bash
# Create database
createdb digital_fte

# Run migrations
alembic upgrade head
```

### 4. Start Services
```bash
# Start backend API server
uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Kafka (if using Docker)
docker-compose up -d kafka zookeeper

# Start Celery worker for background tasks
celery -A backend.src.worker worker --loglevel=info
```

## Frontend Setup (React/Next.js Web Form)

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Environment Configuration
```bash
cp .env.example .env.local
# Edit .env.local with:
# - NEXT_PUBLIC_API_URL: URL of the backend API (default: http://localhost:8000)
```

### 3. Start Development Server
```bash
npm run dev
# Frontend will be available at http://localhost:3000
```

## Docker Compose Setup (Optional)

For a quick all-in-one development setup:
```bash
docker-compose up --build
```

This will start:
- Backend API on port 8000
- Frontend on port 3000
- PostgreSQL on port 5432
- Kafka and Zookeeper
- Mailhog (for email testing) on port 8025

## Running Tests

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Project Structure

```
backend/
├── src/
│   ├── api/          # API route handlers
│   ├── agent/        # OpenAI Agents SDK implementation
│   ├── models/       # Database models
│   ├── services/     # Business logic services
│   ├── worker/       # Celery background tasks
│   └── main.py       # Application entry point
frontend/
├── src/
│   ├── components/   # Reusable UI components
│   ├── pages/        # Next.js pages
│   └── services/     # API service clients
```

## Key Implementation Details

### Message Processing Flow
1. Incoming message received via channel adapter (Gmail, WhatsApp, web form)
2. Message normalized and stored in database
3. Customer identified/created using channel identifiers
4. AI agent processes message:
   - Intent recognition and entity extraction
   - Knowledge base search (semantic + text)
   - Response generation with appropriate tone
   - Sentiment analysis
   - Escalation evaluation
5. Response sent back through same channel
6. Ticket updated with AI response and metadata

### Channel Adapters
- **Gmail Adapter**: Uses Gmail API to poll for new messages in support label
- **WhatsApp Adapter**: Uses Twilio Webhook API for real-time message reception
- **Web Form Adapter**: HTTP endpoint for frontend form submissions

### AI Agent Capabilities
Built with OpenAI Agents SDK featuring:
- Custom function tools for knowledge base search
- Sentiment analysis function
- Escalation decision function
- Response tone adjustment function
- Context management for cross-channel conversations

## Next Steps
1. Review the detailed specification in `spec.md`
2. Examine the data model in `data-model.md`
3. Check API contracts in `contracts/`
4. Refer to the tasks.md file for implementation tasks