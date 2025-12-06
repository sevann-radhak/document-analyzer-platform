import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import pyodbc
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command
from app.core.config import settings
import urllib.parse


def create_database_if_not_exists():
    """Create database if it doesn't exist using pyodbc connection to master."""
    try:
        from app.utils.db_utils import get_available_odbc_driver
        
        db_url = settings.get_database_url()
        
        if "mssql+pyodbc://" in db_url:
            db_url_clean = db_url.replace("mssql+pyodbc://", "")
        elif "sqlserver+pyodbc://" in db_url:
            db_url_clean = db_url.replace("sqlserver+pyodbc://", "")
        else:
            print("✓ Not a SQL Server database, skipping automatic creation.")
            return True
        
        if "@" in db_url_clean:
            auth_part, server_part = db_url_clean.split("@", 1)
            if ":" in auth_part:
                username = auth_part.split(":")[0]
                password = urllib.parse.unquote(auth_part.split(":")[1])
            else:
                username = ""
                password = ""
        else:
            username = ""
            password = ""
            server_part = db_url_clean
        
        if "?" in server_part:
            server_db, query_string = server_part.split("?", 1)
            query_params = urllib.parse.parse_qs(query_string)
            driver = query_params.get("driver", [None])[0]
            if driver:
                driver = urllib.parse.unquote(driver).replace("+", " ")
        else:
            server_db = server_part
            driver = None
        
        if not driver:
            driver = get_available_odbc_driver()
            if not driver:
                raise ValueError("No SQL Server ODBC driver found")
        
        if "/" in server_db:
            server, db_name = server_db.split("/", 1)
        else:
            server = server_db
            db_name = settings.db_database or "document_analyzer"
        
        use_windows_auth = "trusted_connection=yes" in db_url or not username
        if use_windows_auth:
            conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE=master;Trusted_Connection=yes;"
        else:
            conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE=master;UID={username};PWD={password};"
        
        conn = pyodbc.connect(conn_str, timeout=5)
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT name FROM sys.databases WHERE name = ?", (db_name,))
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE [{db_name}]")
            print(f"✓ Database '{db_name}' created successfully")
        else:
            print(f"✓ Database '{db_name}' already exists")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"⚠ Could not create database automatically: {e}")
        print("  Please create the database manually in SQL Server")
        return False


def run_migrations():
    """Run Alembic migrations to create/update database schema."""
    try:
        alembic_cfg = Config("alembic.ini")
        database_url = settings.get_database_url()
        alembic_cfg.attributes['sqlalchemy.url'] = database_url
        command.upgrade(alembic_cfg, "head")
        print("✓ Database migrations executed successfully")
        return True
    except Exception as e:
        print(f"✗ Error running migrations: {e}")
        import traceback
        traceback.print_exc()
        return False


def init_database():
    """Initialize database: create if needed and run migrations."""
    print("Initializing database...")
    
    if create_database_if_not_exists():
        return run_migrations()
    return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)

