"""Global pytest configuration and fixtures."""
import warnings

# Suppress openpyxl deprecation warnings globally
# These warnings come from openpyxl library using deprecated datetime.utcnow()
# The warnings are generated in openpyxl.packaging.core and openpyxl.writer.excel
warnings.filterwarnings("ignore", message=".*datetime.datetime.utcnow.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="openpyxl.packaging.core")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="openpyxl.writer.excel")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="openpyxl")


def pytest_configure(config):
    """Configure pytest hooks."""
    # Additional warning filters for openpyxl
    warnings.filterwarnings("ignore", message=".*datetime.datetime.utcnow.*", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="openpyxl")
