"""CSV validation utility for file upload validation."""
import csv
import io
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from app.schemas.file import ValidationError, ValidationResult
from app.core.constants import ValidationErrorType, ValidationMessages


class CSVValidator:
    """Validates CSV files for empty values, incorrect types, and duplicates."""
    
    def __init__(
        self,
        required_columns: Optional[List[str]] = None,
        column_types: Optional[Dict[str, type]] = None,
        unique_columns: Optional[List[str]] = None
    ):
        """
        Initialize CSV validator.
        
        Args:
            required_columns: List of column names that cannot be empty
            column_types: Dictionary mapping column names to expected types
            unique_columns: List of column names that must be unique across rows
        """
        self.required_columns = required_columns or []
        self.column_types = column_types or {}
        self.unique_columns = unique_columns or []
    
    def validate_file(
        self,
        file_content: bytes,
        encoding: str = "utf-8",
        delimiter: str = ","
    ) -> ValidationResult:
        """
        Validate a CSV file and return validation results.
        
        Args:
            file_content: CSV file content as bytes
            encoding: File encoding (default: utf-8)
            delimiter: CSV delimiter (default: comma)
        
        Returns:
            ValidationResult with all validation errors found
        """
        empty_errors: List[ValidationError] = []
        type_errors: List[ValidationError] = []
        duplicate_errors: List[ValidationError] = []
        
        try:
            content_str = file_content.decode(encoding)
            reader = csv.DictReader(io.StringIO(content_str), delimiter=delimiter)
            
            if not reader.fieldnames:
                return ValidationResult(
                    is_valid=False,
                    total_rows=0,
                    total_errors=1,
                    empty_value_errors=[],
                    incorrect_type_errors=[],
                    duplicate_errors=[]
                )
            
            rows = list(reader)
            total_rows = len(rows)
            
            seen_values: Dict[str, Set[Any]] = {
                col: set() for col in self.unique_columns
            }
            
            for row_index, row in enumerate(rows, start=2):
                row_num = row_index
                
                for column_name, value in row.items():
                    value_stripped = value.strip() if value else ""
                    
                    empty_error = self._validate_empty(
                        row_num, column_name, value_stripped
                    )
                    if empty_error:
                        empty_errors.append(empty_error)
                    
                    type_error = self._validate_type(
                        row_num, column_name, value_stripped
                    )
                    if type_error:
                        type_errors.append(type_error)
                    
                    duplicate_error = self._validate_duplicate(
                        row_num, column_name, value_stripped, seen_values
                    )
                    if duplicate_error:
                        duplicate_errors.append(duplicate_error)
            
            total_errors = len(empty_errors) + len(type_errors) + len(duplicate_errors)
            
            return ValidationResult(
                is_valid=total_errors == 0,
                total_rows=total_rows,
                total_errors=total_errors,
                empty_value_errors=empty_errors,
                incorrect_type_errors=type_errors,
                duplicate_errors=duplicate_errors
            )
        
        except UnicodeDecodeError as e:
            return ValidationResult(
                is_valid=False,
                total_rows=0,
                total_errors=1,
                empty_value_errors=[],
                incorrect_type_errors=[],
                duplicate_errors=[]
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                total_rows=0,
                total_errors=1,
                empty_value_errors=[],
                incorrect_type_errors=[],
                duplicate_errors=[]
            )
    
    def _validate_empty(
        self,
        row: int,
        column: str,
        value: str
    ) -> Optional[ValidationError]:
        """
        Validate if a required column has an empty value.
        
        Args:
            row: Row number (1-indexed, including header)
            column: Column name
            value: Cell value
        
        Returns:
            ValidationError if empty, None otherwise
        """
        if column in self.required_columns and not value:
            return ValidationError(
                row=row,
                column=column,
                error_type=ValidationErrorType.EMPTY,
                message=ValidationMessages.FIELD_REQUIRED.format(field=column),
                value=None
            )
        return None
    
    def _validate_type(
        self,
        row: int,
        column: str,
        value: str
    ) -> Optional[ValidationError]:
        """
        Validate if a value matches the expected type for its column.
        
        Args:
            row: Row number (1-indexed, including header)
            column: Column name
            value: Cell value
        
        Returns:
            ValidationError if type mismatch, None otherwise
        """
        if column not in self.column_types or not value:
            return None
        
        expected_type = self.column_types[column]
        
        try:
            if expected_type == int:
                int(value)
            elif expected_type == float:
                float(value)
            elif expected_type == bool:
                self._parse_bool(value)
            elif expected_type == datetime:
                self._parse_datetime(value)
            return None
        except (ValueError, TypeError):
            actual_type = type(value).__name__
            return ValidationError(
                row=row,
                column=column,
                error_type=ValidationErrorType.INCORRECT_TYPE,
                message=ValidationMessages.EXPECTED_TYPE_GOT.format(
                    expected_type=expected_type.__name__,
                    actual_type=actual_type
                ),
                value=value
            )
    
    def _validate_duplicate(
        self,
        row: int,
        column: str,
        value: str,
        seen_values: Dict[str, Set[Any]]
    ) -> Optional[ValidationError]:
        """
        Validate if a value in a unique column is duplicated.
        
        Args:
            row: Row number (1-indexed, including header)
            column: Column name
            value: Cell value
            seen_values: Dictionary tracking seen values per column
        
        Returns:
            ValidationError if duplicate found, None otherwise
        """
        if column not in self.unique_columns or not value:
            return None
        
        normalized_value = self._normalize_value(value)
        
        if normalized_value in seen_values[column]:
            return ValidationError(
                row=row,
                column=column,
                error_type=ValidationErrorType.DUPLICATE,
                message=ValidationMessages.DUPLICATE_VALUE.format(field=column),
                value=value
            )
        
        seen_values[column].add(normalized_value)
        return None
    
    def _parse_bool(self, value: str) -> bool:
        """
        Parse a string value to boolean.
        
        Args:
            value: String value to parse
        
        Returns:
            Boolean value
        
        Raises:
            ValueError: If value cannot be parsed as boolean
        """
        value_lower = value.lower().strip()
        if value_lower in ("true", "1", "yes", "y", "on"):
            return True
        if value_lower in ("false", "0", "no", "n", "off"):
            return False
        raise ValueError(f"Cannot parse '{value}' as boolean")
    
    def _parse_datetime(self, value: str) -> datetime:
        """
        Parse a string value to datetime.
        
        Args:
            value: String value to parse
        
        Returns:
            Datetime object
        
        Raises:
            ValueError: If value cannot be parsed as datetime
        """
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y/%m/%d"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Cannot parse '{value}' as datetime")
    
    def _normalize_value(self, value: str) -> Any:
        """
        Normalize a value for duplicate comparison.
        
        Args:
            value: Value to normalize
        
        Returns:
            Normalized value (lowercase string for case-insensitive comparison)
        """
        if isinstance(value, str):
            return value.lower().strip()
        return value


def validate_csv(
    file_content: bytes,
    required_columns: Optional[List[str]] = None,
    column_types: Optional[Dict[str, type]] = None,
    unique_columns: Optional[List[str]] = None,
    encoding: str = "utf-8",
    delimiter: str = ","
) -> ValidationResult:
    """
    Convenience function to validate a CSV file.
    
    Args:
        file_content: CSV file content as bytes
        required_columns: List of column names that cannot be empty
        column_types: Dictionary mapping column names to expected types
        unique_columns: List of column names that must be unique across rows
        encoding: File encoding (default: utf-8)
        delimiter: CSV delimiter (default: comma)
    
    Returns:
        ValidationResult with all validation errors found
    """
    validator = CSVValidator(
        required_columns=required_columns,
        column_types=column_types,
        unique_columns=unique_columns
    )
    return validator.validate_file(file_content, encoding=encoding, delimiter=delimiter)

