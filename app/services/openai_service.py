"""OpenAI implementation of AI service interface."""
import base64
import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from openai import APIError, APIConnectionError, APITimeoutError

from app.services.ai_service import (
    AIServiceInterface,
    DocumentClassification,
    SentimentType
)
from app.core.config import settings
from app.core.constants import ErrorMessages


class OpenAIService(AIServiceInterface):
    """OpenAI implementation of AI document analysis service."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI service.

        Args:
            api_key: OpenAI API key. If not provided, uses settings.openai_api_key
        """
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise ValueError(ErrorMessages.OPENAI_API_KEY_REQUIRED)
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = "gpt-4o"

    def _get_mime_type(self, filename: str) -> str:
        """
        Get MIME type based on file extension.

        Args:
            filename: File name with extension

        Returns:
            MIME type string
        """
        extension = filename.lower().split('.')[-1]
        mime_types = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png'
        }
        return mime_types.get(extension, 'application/octet-stream')

    def _is_image(self, filename: str) -> bool:
        """
        Check if file is an image.

        Args:
            filename: File name with extension

        Returns:
            True if image, False otherwise
        """
        extension = filename.lower().split('.')[-1]
        return extension in ['jpg', 'jpeg', 'png']

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
        try:
            mime_type = self._get_mime_type(filename)
            
            if self._is_image(filename):
                base64_image = base64.b64encode(file_content).decode('utf-8')
                image_url = f"data:{mime_type};base64,{base64_image}"
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a document classification expert. Analyze the document and classify it as either 'Invoice' (if it contains economic/financial data like invoices, bills, receipts) or 'Information' (if it contains general text, articles, reports, letters). Respond with only one word: 'Invoice' or 'Information'."
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": image_url}
                                },
                                {
                                    "type": "text",
                                    "text": "Classify this document as 'Invoice' or 'Information'."
                                }
                            ]
                        }
                    ],
                    max_tokens=10
                )
            else:
                raise ValueError(
                    ErrorMessages.AI_UNSUPPORTED_FILE_TYPE.format(file_type=filename.split('.')[-1])
                )

            classification_text = response.choices[0].message.content.strip().lower()
            
            if 'invoice' in classification_text:
                return DocumentClassification.INVOICE
            elif 'information' in classification_text:
                return DocumentClassification.INFORMATION
            else:
                raise ValueError(
                    ErrorMessages.AI_CLASSIFICATION_ERROR.format(
                        error=f"Unexpected classification result: {classification_text}"
                    )
                )

        except (APIError, APIConnectionError, APITimeoutError) as e:
            raise ValueError(
                ErrorMessages.AI_CLASSIFICATION_ERROR.format(error=str(e))
            ) from e
        except Exception as e:
            raise ValueError(
                ErrorMessages.AI_DOCUMENT_PROCESSING_ERROR.format(error=str(e))
            ) from e

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
            Dictionary containing invoice data

        Raises:
            ValueError: If document is not an invoice or cannot be processed
            Exception: For AI service-specific errors
        """
        try:
            mime_type = self._get_mime_type(filename)
            
            if not self._is_image(filename):
                raise ValueError(
                    ErrorMessages.AI_UNSUPPORTED_FILE_TYPE.format(file_type=filename.split('.')[-1])
                )

            base64_image = base64.b64encode(file_content).decode('utf-8')
            image_url = f"data:{mime_type};base64,{base64_image}"

            prompt = """Extract structured data from this invoice document. Return a JSON object with the following structure:
{
    "client": {"name": "...", "address": "..."},
    "provider": {"name": "...", "address": "..."},
    "invoice_number": "...",
    "date": "...",
    "products": [
        {"quantity": 0, "name": "...", "unit_price": 0.0, "total": 0.0}
    ],
    "invoice_total": 0.0
}

If any field is not found, use null or empty string. Return only valid JSON, no additional text."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting structured data from invoices. Always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=2000
            )

            response_text = response.choices[0].message.content.strip()
            
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()

            extracted_data = json.loads(response_text)
            
            return {
                "client": extracted_data.get("client", {"name": "", "address": ""}),
                "provider": extracted_data.get("provider", {"name": "", "address": ""}),
                "invoice_number": extracted_data.get("invoice_number", ""),
                "date": extracted_data.get("date", ""),
                "products": extracted_data.get("products", []),
                "invoice_total": float(extracted_data.get("invoice_total", 0.0))
            }

        except json.JSONDecodeError as e:
            raise ValueError(
                ErrorMessages.AI_EXTRACTION_ERROR.format(
                    error=f"Failed to parse JSON response: {str(e)}"
                )
            ) from e
        except (APIError, APIConnectionError, APITimeoutError) as e:
            raise ValueError(
                ErrorMessages.AI_EXTRACTION_ERROR.format(error=str(e))
            ) from e
        except Exception as e:
            raise ValueError(
                ErrorMessages.AI_DOCUMENT_PROCESSING_ERROR.format(error=str(e))
            ) from e

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
            Dictionary containing information data

        Raises:
            ValueError: If document cannot be processed
            Exception: For AI service-specific errors
        """
        try:
            mime_type = self._get_mime_type(filename)
            
            if not self._is_image(filename):
                raise ValueError(
                    ErrorMessages.AI_UNSUPPORTED_FILE_TYPE.format(file_type=filename.split('.')[-1])
                )

            base64_image = base64.b64encode(file_content).decode('utf-8')
            image_url = f"data:{mime_type};base64,{base64_image}"

            prompt = """Extract structured data from this document. Return a JSON object with the following structure:
{
    "description": "...",
    "content_summary": "...",
    "sentiment": "positive" | "negative" | "neutral"
}

Analyze the sentiment of the document content. Return only valid JSON, no additional text."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing documents and extracting summaries. Always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=1000
            )

            response_text = response.choices[0].message.content.strip()
            
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()

            extracted_data = json.loads(response_text)
            
            sentiment_str = extracted_data.get("sentiment", "neutral").lower()
            sentiment = SentimentType.NEUTRAL
            if sentiment_str == "positive":
                sentiment = SentimentType.POSITIVE
            elif sentiment_str == "negative":
                sentiment = SentimentType.NEGATIVE
            
            return {
                "description": extracted_data.get("description", ""),
                "content_summary": extracted_data.get("content_summary", ""),
                "sentiment": sentiment
            }

        except json.JSONDecodeError as e:
            raise ValueError(
                ErrorMessages.AI_EXTRACTION_ERROR.format(
                    error=f"Failed to parse JSON response: {str(e)}"
                )
            ) from e
        except (APIError, APIConnectionError, APITimeoutError) as e:
            raise ValueError(
                ErrorMessages.AI_EXTRACTION_ERROR.format(error=str(e))
            ) from e
        except Exception as e:
            raise ValueError(
                ErrorMessages.AI_DOCUMENT_PROCESSING_ERROR.format(error=str(e))
            ) from e

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
            Dictionary containing classification and extracted data

        Raises:
            ValueError: If document cannot be processed
            Exception: For AI service-specific errors
        """
        classification = await self.classify_document(file_content, filename)
        
        if classification == DocumentClassification.INVOICE:
            extracted_data = await self.extract_invoice_data(file_content, filename)
        else:
            extracted_data = await self.extract_information_data(file_content, filename)
        
        return {
            "classification": classification,
            "extracted_data": extracted_data
        }

