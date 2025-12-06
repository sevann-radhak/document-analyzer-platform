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
- Automatic database initialization and migrations

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
├── scripts/
│   └── init_db.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── alembic/
│   └── versions/
├── requirements.txt
├── .env.example
└── README.md
```

## Prerequisites

- Python 3.11+
- SQL Server (2019 or later)
- ODBC Driver 17 for SQL Server (or later)
- AWS Account (for S3) - Optional for development
- AI Service API Key (OpenAI or Azure Cognitive Services) - Optional for development

## Quick Start

### 1. SQL Server Setup

#### Option A: SQL Server Authentication (Recommended for portability)

1. **Enable SQL Server Authentication:**
   - Open SQL Server Management Studio (SSMS)
   - Right-click on server → Properties → Security
   - Select "SQL Server and Windows Authentication mode"
   - Click OK and restart SQL Server service

2. **Create Application User:**
   - In SSMS: Security → Logins → New Login
   - Login name: Choose your username (e.g., `app_user`)
   - Select "SQL Server authentication"
   - Password: Choose a strong password
   - Uncheck "Enforce password policy" (development only)
   - Server Roles → Check "dbcreator"
   - Click OK

#### Option B: Windows Authentication (Local development only)

- No additional setup needed if using Windows Authentication
- Update `.env` to use `trusted_connection=yes` in DATABASE_URL

### 2. Project Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd document-analyzer-platform
```

2. **Create virtual environment:**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
```bash
# Copy example file
cp .env.example .env

# Edit .env with your settings
# Option 1: Complete connection string (full control)
# DATABASE_URL=mssql+pyodbc://username:password@server/database_name?driver=ODBC+Driver+17+for+SQL+Server

# Option 2: Individual components (recommended - auto-detects driver)
DB_SERVER=localhost
DB_DATABASE=document_analyzer
DB_USERNAME=your_db_username
DB_PASSWORD=your_db_password
DB_USE_WINDOWS_AUTH=False
AUTO_INIT_DB=True
```

**Note**: Option 2 automatically detects the best available ODBC driver (17, 18, 13, etc.), making it more portable across different machines.

5. **Run the application:**
```bash
uvicorn app.main:app --reload
```

The application will automatically:
- Create the database if it doesn't exist
- Run all migrations to create tables
- Start the API server

The API will be available at `http://localhost:8000`

### 3. Manual Database Initialization (Optional)

If you prefer to initialize the database manually:

```bash
python scripts/init_db.py
```

## API Documentation

Once the application is running, access the interactive API documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Environment Variables

See `.env.example` for all available environment variables:

- `DATABASE_URL`: SQL Server connection string
- `AWS_ACCESS_KEY_ID`: AWS credentials for S3
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_S3_BUCKET_NAME`: S3 bucket name
- `JWT_SECRET_KEY`: Secret key for JWT tokens
- `OPENAI_API_KEY`: OpenAI API key (optional)
- `AZURE_COGNITIVE_SERVICES_KEY`: Azure key (optional)

## Testing

Run tests with pytest:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

## Database Migrations

Migrations are handled automatically on startup. To run manually:

```bash
# Apply all migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1
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

## Production Deployment

For production environments:

1. Set `AUTO_INIT_DB=false` in environment variables
2. Run migrations manually in deployment pipeline:
   ```bash
   python scripts/init_db.py
   ```
3. Use proper secrets management (AWS Secrets Manager, Azure Key Vault, etc.)
4. Configure proper CORS origins
5. Use production-grade JWT secret keys

## Troubleshooting

### Database Connection Issues

- Verify SQL Server is running
- Check ODBC Driver 17 is installed: `python -c "import pyodbc; print(pyodbc.drivers())"`
- Verify connection string format in `.env`
- Check user permissions in SQL Server

### Migration Issues

- Ensure database exists before running migrations
- Check Alembic configuration in `alembic.ini`
- Verify all models are imported in `alembic/env.py`

## License

[Add license information]
