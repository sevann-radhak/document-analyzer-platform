import pyodbc
from typing import Optional


def get_available_odbc_driver() -> Optional[str]:
    """Detect available SQL Server ODBC driver, prioritizing newer versions."""
    available_drivers = pyodbc.drivers()
    
    preferred_drivers = [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 13 for SQL Server",
        "SQL Server Native Client 11.0",
        "SQL Server",
    ]
    
    for driver in preferred_drivers:
        if driver in available_drivers:
            return driver
    
    sql_server_drivers = [d for d in available_drivers if "SQL Server" in d]
    if sql_server_drivers:
        return sql_server_drivers[0]
    
    return None


def build_database_url(
    username: Optional[str],
    password: Optional[str],
    server: str,
    database: str,
    use_windows_auth: bool = False,
    driver: Optional[str] = None
) -> str:
    """Build SQL Server connection URL with automatic driver detection."""
    if driver is None:
        driver = get_available_odbc_driver()
        if driver is None:
            raise ValueError(
                "No SQL Server ODBC driver found. "
                "Please install ODBC Driver 17 or 18 for SQL Server. "
                "Download: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server"
            )
    
    driver_encoded = driver.replace(" ", "+")
    
    if use_windows_auth:
        url = f"mssql+pyodbc://@{server}/{database}?driver={driver_encoded}&trusted_connection=yes"
    else:
        if not username or not password:
            raise ValueError("Username and password are required when not using Windows Authentication")
        from urllib.parse import quote_plus
        encoded_password = quote_plus(password)
        url = f"mssql+pyodbc://{username}:{encoded_password}@{server}/{database}?driver={driver_encoded}"
    
    return url

