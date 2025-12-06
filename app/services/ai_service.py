"""AI service interface for document analysis."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Literal
from enum import Enum


class DocumentClassification(str, Enum):
    """Document classification types."""
    INVOICE = "Invoice"
    INFORMATION = "Information"


class SentimentType(str, Enum):
    """Sentiment analysis types."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class AIServiceInterface(ABC):
    """Abstract interface for AI document analysis services."""

    @abstractmethod
    async def classify_document(
        self,
        file_content: bytes,
        filename: str
    ) -> DocumentClassification:
        """
        Classify a document as Invoice or Information.

        Args:
            file_content: Raw file content as bytes
            filename: Original filename with extension

        Returns:
            DocumentClassification enum value (INVOICE or INFORMATION)

        Raises:
            ValueError: If document cannot be processed or classified
            Exception: For AI service-specific errors
        """
        pass

    @abstractmethod
    async def extract_invoice_data(
        self,
        file_content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Extract structured data from an Invoice document.

        Args:
            file_content: Raw file content as bytes
            filename: Original filename with extension

        Returns:
            Dictionary containing:
                - client: Dict with "name" and "address"
                - provider: Dict with "name" and "address"
                - invoice_number: str
                - date: str (ISO format or date string)
                - products: List of Dict with "quantity", "name", "unit_price", "total"
                - invoice_total: float

        Raises:
            ValueError: If document is not an invoice or cannot be processed
            Exception: For AI service-specific errors
        """
        pass

    @abstractmethod
    async def extract_information_data(
        self,
        file_content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Extract structured data from an Information document.

        Args:
            file_content: Raw file content as bytes
            filename: Original filename with extension

        Returns:
            Dictionary containing:
                - description: str
                - content_summary: str
                - sentiment: SentimentType enum value (positive, negative, neutral)

        Raises:
            ValueError: If document cannot be processed
            Exception: For AI service-specific errors
        """
        pass

    @abstractmethod
    async def analyze_document(
        self,
        file_content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Complete document analysis: classify and extract data.

        Args:
            file_content: Raw file content as bytes
            filename: Original filename with extension

        Returns:
            Dictionary containing:
                - classification: DocumentClassification enum value
                - extracted_data: Dict with extracted data based on classification

        Raises:
            ValueError: If document cannot be processed
            Exception: For AI service-specific errors
        """
        pass

