# College Department AI Chatbot System

An enterprise-level intelligent conversational platform designed to serve college departments with comprehensive data integration, AI-powered analysis, and multi-user support.

## Architecture

The system follows a microservice architecture with the following services:

- **Authentication Service** (Port 8000): User authentication, authorization, and session management
- **Chat Service** (Port 8001): Core chatbot functionality and conversation management
- **RAG Pipeline Service** (Port 8002): Retrieval-Augmented Generation for intelligent responses
- **Document Processing Service** (Port 8003): Document ingestion, processing, and knowledge base management
- **Notification Service** (Port 8004): Multi-channel notification delivery and management
- **Admin Service** (Port 8005): Administrative interface and system management
- **Analytics Service** (Port 8006): System monitoring, metrics collection, and reporting

## Technology Stack

- **Backend Framework**: FastAPI
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Vector Database**: ChromaDB
- **Task Queue**: Celery
- **Containerization**: Docker & Docker Compose
- **Orchestration**: Kubernetes (production)

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+ (if running locally without Docker)
- Redis 7+ (if running locally without Docker)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd college-ai-chatbot-system
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Using Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### 4. Local Development Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (after setting up PostgreSQL)
alembic upgrade head

# Run individual services
python auth_service/main.py
python chat_service/main.py
python rag_service/main.py
# ... etc
```

## Project Structure

```
college-ai-chatbot-system/
├── auth_service/           # Authentication and authorization
│   ├── __init__.py
│   ├── main.py
│   └── Dockerfile
├── chat_service/           # Chat functionality
│   ├── __init__.py
│   ├── main.py
│   └── Dockerfile
├── rag_service/            # RAG pipeline
│   ├── __init__.py
│   ├── main.py
│   └── Dockerfile
├── document_service/       # Document processing
│   ├── __init__.py
│   ├── main.py
│   └── Dockerfile
├── notification_service/   # Notifications
│   ├── __init__.py
│   ├── main.py
│   └── Dockerfile
├── admin_service/          # Admin interface
│   ├── __init__.py
│   ├── main.py
│   └── Dockerfile
├── analytics_service/      # Analytics and monitoring
│   ├── __init__.py
│   ├── main.py
│   └── Dockerfile
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Docker Compose configuration
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Service Endpoints

Once running, services are available at:

- Authentication Service: http://localhost:8000
- Chat Service: http://localhost:8001
- RAG Pipeline Service: http://localhost:8002
- Document Processing Service: http://localhost:8003
- Notification Service: http://localhost:8004
- Admin Service: http://localhost:8005
- Analytics Service: http://localhost:8006

API documentation (Swagger UI) for each service:
- http://localhost:8000/docs
- http://localhost:8001/docs
- ... etc

## Health Checks

Each service provides a health check endpoint:

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
# ... etc
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type checking
mypy .
```

## Configuration

Key configuration options in `.env`:

- **Database**: PostgreSQL connection settings
- **Redis**: Cache and session store settings
- **Vector DB**: ChromaDB configuration
- **Authentication**: JWT settings, password policies
- **File Upload**: Size limits, allowed extensions
- **AI/LLM**: OpenAI API key and model settings
- **External APIs**: ERP, Notice Board, Attendance system integration

## Deployment

### Docker Compose (Development/Testing)

```bash
docker-compose up -d
```

### Kubernetes (Production)

Kubernetes manifests will be created in subsequent tasks. The system is designed for horizontal scaling with:

- Multiple replicas per service
- Load balancing
- Auto-scaling based on metrics
- Zero-downtime deployments

## Security

- JWT-based authentication
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Rate limiting
- Data encryption at rest and in transit
- Security audit logging

## Monitoring

- Prometheus metrics collection
- Grafana dashboards
- Elasticsearch log aggregation
- Health check endpoints
- Performance monitoring

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions, please contact [support contact].
