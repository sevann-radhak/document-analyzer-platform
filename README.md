# Document Analyzer Platform

A FastAPI-based document analysis platform with AI integration, following Clean Architecture principles.

## Features

- REST API for authentication and file management
- Document analysis with AI (PDF, JPG, PNG)
- Automatic document classification (Invoice/Information)
- Data extraction from documents
- Event logging and historical tracking
- AWS S3 integration for file storage
- SQL Server database with SQLAlchemy ORM
- JWT-based authentication with role-based access control

## Project Structure

```
document-analyzer-platform/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── dependencies.py
│   ├── services/
│   ├── repositories/
│   ├── models/
│   ├── schemas/
│   ├── utils/
│   └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

### Prerequisites

- Python 3.11+
- SQL Server
- AWS Account (for S3)
- AI Service API Key (OpenAI or Azure Cognitive Services)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd document-analyzer-platform
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- Database connection string
- AWS credentials
- JWT secret key
- AI service API keys

5. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the application is running, access the interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run tests with pytest:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

## Architecture

This project follows Clean Architecture principles:

- **API Layer** (`app/api/`): HTTP endpoints and request/response handling
- **Services Layer** (`app/services/`): Business logic and use cases
- **Repositories Layer** (`app/repositories/`): Data access abstraction
- **Models Layer** (`app/models/`): Domain models and database entities
- **Schemas Layer** (`app/schemas/`): Pydantic models for validation
- **Core Layer** (`app/core/`): Configuration, security, and shared utilities

## Development

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write unit tests for all business logic
- Make small, granular commits
- Document AI-assisted changes in commit messages

## License

[Add license information]

