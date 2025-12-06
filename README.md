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

## API Usage Examples

### Authentication Flow

#### 1. Anonymous Login
Get a JWT token by performing anonymous login (no credentials required):

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**
```json
{
  "id_usuario": 1,
  "rol": "user",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 15
}
```

#### 2. Refresh Token
Renew your JWT token before it expires:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 15
}
```

### File Upload

#### Upload CSV File
Upload and validate a CSV file:

```bash
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@data.csv" \
  -F "param1=value1" \
  -F "param2=value2"
```

**Response:**
```json
{
  "file_id": 1,
  "filename": "data.csv",
  "s3_key": "uploads/2024/12/data_1234567890.csv",
  "uploaded_at": "2024-12-06T10:30:00Z",
  "validation_results": {
    "is_valid": true,
    "empty_values": [],
    "incorrect_types": [],
    "duplicates": []
  },
  "param1": "value1",
  "param2": "value2"
}
```

### Document Analysis

#### Upload and Analyze Document
Upload a document (PDF, JPG, or PNG) for AI analysis:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@invoice.pdf"
```

**Response (Invoice):**
```json
{
  "document_id": 1,
  "filename": "invoice.pdf",
  "file_type": "PDF",
  "s3_key": "documents/2024/12/invoice_1234567890.pdf",
  "classification": "Invoice",
  "extracted_data": {
    "client": {
      "name": "John Doe",
      "address": "123 Main St, City, State 12345"
    },
    "provider": {
      "name": "ABC Company Inc.",
      "address": "456 Business Ave, City, State 67890"
    },
    "invoice_number": "INV-2024-001",
    "date": "2024-12-06",
    "products": [
      {
        "quantity": 2,
        "name": "Product A",
        "unit_price": 29.99,
        "total": 59.98
      }
    ],
    "invoice_total": 59.98
  },
  "uploaded_at": "2024-12-06T10:30:00Z"
}
```

**Response (Information Document):**
```json
{
  "document_id": 2,
  "filename": "report.png",
  "file_type": "PNG",
  "s3_key": "documents/2024/12/report_1234567890.png",
  "classification": "Information",
  "extracted_data": {
    "description": "Meeting minutes from Q4 planning",
    "content_summary": "The meeting covered Q4 financial results...",
    "sentiment": "neutral"
  },
  "uploaded_at": "2024-12-06T10:30:00Z"
}
```

### Event History

#### Get Event Log
Retrieve event log with optional filters:

```bash
curl -X GET "http://localhost:8000/api/v1/events?event_type=Document%20upload&start_date=2024-12-01T00:00:00Z&limit=50" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "events": [
    {
      "id": 1,
      "event_type": "Document upload",
      "description": "Document 'invoice.pdf' uploaded and classified as 'Invoice'. Document ID: 1",
      "user_id": 1,
      "created_at": "2024-12-06T10:30:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

#### Export Events to Excel
Export filtered events to Excel format:

```bash
curl -X GET "http://localhost:8000/api/v1/events/export?event_type=Document%20upload&start_date=2024-12-01T00:00:00Z" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --output events.xlsx
```

### Python Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. Login
response = requests.post(f"{BASE_URL}/auth/login", json={})
data = response.json()
token = data["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Upload CSV file
with open("data.csv", "rb") as f:
    files = {"file": f}
    data = {"param1": "value1", "param2": "value2"}
    response = requests.post(
        f"{BASE_URL}/files/upload",
        headers=headers,
        files=files,
        data=data
    )
    print(response.json())

# 3. Upload and analyze document
with open("invoice.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"{BASE_URL}/documents/upload",
        headers=headers,
        files=files
    )
    print(response.json())

# 4. Get events
response = requests.get(
    f"{BASE_URL}/events",
    headers=headers,
    params={"event_type": "Document upload", "limit": 10}
)
print(response.json())
```

## Environment Variables

See `.env.example` for all available environment variables with detailed descriptions.

### Required Variables

**Database (choose one approach):**
- Option 1: `DATABASE_URL` - Complete SQL Server connection string
- Option 2: Individual components (recommended):
  - `DB_SERVER` - SQL Server hostname or IP
  - `DB_DATABASE` - Database name
  - `DB_USERNAME` - Database username (if not using Windows Auth)
  - `DB_PASSWORD` - Database password (if not using Windows Auth)
  - `DB_USE_WINDOWS_AUTH` - Set to `True` for Windows Authentication
  - `AUTO_INIT_DB` - Set to `True` to auto-initialize database on startup

**AWS S3:**
- `AWS_ACCESS_KEY_ID` - AWS access key for S3 operations
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_S3_BUCKET_NAME` - S3 bucket name for file storage
- `AWS_REGION` - AWS region (default: `us-east-1`)

**JWT Authentication:**
- `JWT_SECRET_KEY` - Secret key for JWT token signing (minimum 32 characters)
- `JWT_ALGORITHM` - JWT algorithm (default: `HS256`)
- `JWT_EXPIRATION_MINUTES` - Token expiration time in minutes (default: `15`)

**AI Services:**
- `OPENAI_API_KEY` - OpenAI API key for document analysis (required for AI features)

### Optional Variables

- `AZURE_COGNITIVE_SERVICES_KEY` - Azure Cognitive Services key (alternative to OpenAI)
- `AZURE_COGNITIVE_SERVICES_ENDPOINT` - Azure Cognitive Services endpoint
- `DB_DRIVER` - Custom ODBC driver (auto-detected if not specified)
- `APP_NAME` - Application name (default: `Document Analyzer Platform`)
- `APP_VERSION` - Application version (default: `1.0.0`)
- `DEBUG` - Enable debug mode (default: `False`)
- `LOG_LEVEL` - Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (default: `INFO`)

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

### Pre-Deployment Checklist

1. **Environment Variables**
   - Set `AUTO_INIT_DB=False` to disable automatic database initialization
   - Use strong `JWT_SECRET_KEY` (minimum 32 characters, randomly generated)
   - Set `DEBUG=False` for production
   - Configure `LOG_LEVEL=INFO` or `WARNING` for production
   - Use production database credentials (never use development credentials)

2. **Database Setup**
   - Create production database manually
   - Run migrations manually in deployment pipeline:
     ```bash
     python scripts/init_db.py
     ```
   - Or use Alembic directly:
     ```bash
     alembic upgrade head
     ```

3. **Secrets Management**
   - Use proper secrets management (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault, etc.)
   - Never commit `.env` files to version control
   - Rotate secrets regularly
   - Use different secrets for each environment (dev, staging, prod)

4. **AWS S3 Configuration**
   - Create dedicated S3 bucket for production
   - Configure bucket policies and IAM roles properly
   - Enable versioning and lifecycle policies
   - Set up CloudWatch monitoring for S3 operations

5. **Security**
   - Configure proper CORS origins (restrict to your frontend domain)
   - Use HTTPS only (configure reverse proxy with SSL/TLS)
   - Set up rate limiting
   - Enable API authentication for all endpoints
   - Review and restrict user roles and permissions

6. **Monitoring and Logging**
   - Set up application monitoring (CloudWatch, Datadog, New Relic, etc.)
   - Configure log aggregation
   - Set up alerts for errors and performance issues
   - Monitor database connection pool usage

### Deployment Options

#### Option 1: Docker Deployment

1. **Build Docker image:**
   ```bash
   docker build -t document-analyzer-platform:latest .
   ```

2. **Run container:**
   ```bash
   docker run -d \
     --name document-analyzer \
     -p 8000:8000 \
     --env-file .env.production \
     document-analyzer-platform:latest
   ```

3. **Using Docker Compose:**
   ```bash
   docker-compose up -d
   ```

#### Option 2: Systemd Service (Linux)

1. **Create service file** `/etc/systemd/system/document-analyzer.service`:
   ```ini
   [Unit]
   Description=Document Analyzer Platform API
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/opt/document-analyzer-platform
   Environment="PATH=/opt/document-analyzer-platform/venv/bin"
   ExecStart=/opt/document-analyzer-platform/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

2. **Enable and start service:**
   ```bash
   sudo systemctl enable document-analyzer
   sudo systemctl start document-analyzer
   ```

#### Option 3: Cloud Platform Deployment

**AWS (Elastic Beanstalk / ECS / EC2):**
- Use AWS Secrets Manager for environment variables
- Configure Application Load Balancer with SSL
- Set up Auto Scaling groups
- Use RDS for SQL Server
- Configure CloudWatch for monitoring

**Azure (App Service / Container Instances):**
- Use Azure Key Vault for secrets
- Configure Application Gateway with SSL
- Use Azure SQL Database
- Set up Application Insights for monitoring

**Google Cloud (Cloud Run / GKE):**
- Use Secret Manager for environment variables
- Configure Cloud Load Balancing with SSL
- Use Cloud SQL for SQL Server
- Set up Cloud Monitoring

### Post-Deployment Verification

1. **Health Check:**
   ```bash
   curl http://your-domain/api/v1/auth/login -X POST -H "Content-Type: application/json" -d '{}'
   ```

2. **Verify Database Connection:**
   - Check application logs for database connection errors
   - Verify migrations were applied correctly

3. **Test API Endpoints:**
   - Test authentication flow
   - Test file upload
   - Test document analysis
   - Verify event logging

4. **Monitor Performance:**
   - Check response times
   - Monitor error rates
   - Review resource usage (CPU, memory, database connections)

### Backup and Recovery

1. **Database Backups:**
   - Set up automated database backups
   - Test backup restoration procedures
   - Store backups in secure, separate location

2. **S3 Backup:**
   - Enable S3 versioning
   - Configure cross-region replication if needed
   - Set up lifecycle policies for old files

3. **Application State:**
   - Document all configuration changes
   - Keep deployment scripts versioned
   - Maintain rollback procedures

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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
