"""Document analysis schemas."""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Union
from datetime import datetime
from app.services.ai_service import DocumentClassification, SentimentType


class DocumentUploadRequest(BaseModel):
    """Request schema for document upload endpoint.
    
    Note: In FastAPI, file uploads use UploadFile from fastapi.
    This schema is for documentation purposes.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "Upload a PDF, JPG, or PNG document for AI analysis"
            }
        }
    )


class ClientInfo(BaseModel):
    """Schema for client information in invoices."""
    
    name: str = Field(..., description="Client name")
    address: str = Field(..., description="Client address")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "John Doe",
                "address": "123 Main St, City, State 12345"
            }
        }
    )


class ProviderInfo(BaseModel):
    """Schema for provider information in invoices."""
    
    name: str = Field(..., description="Provider name")
    address: str = Field(..., description="Provider address")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "ABC Company Inc.",
                "address": "456 Business Ave, City, State 67890"
            }
        }
    )


class ProductItem(BaseModel):
    """Schema for product/item in invoice."""
    
    quantity: int = Field(..., description="Product quantity", ge=0)
    name: str = Field(..., description="Product name")
    unit_price: float = Field(..., description="Unit price", ge=0.0)
    total: float = Field(..., description="Total price for this item", ge=0.0)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "quantity": 2,
                "name": "Product Name",
                "unit_price": 29.99,
                "total": 59.98
            }
        }
    )


class InvoiceData(BaseModel):
    """Schema for extracted invoice data."""
    
    client: ClientInfo = Field(..., description="Client information")
    provider: ProviderInfo = Field(..., description="Provider information")
    invoice_number: str = Field(..., description="Invoice number")
    date: str = Field(..., description="Invoice date (ISO format or date string)")
    products: List[ProductItem] = Field(
        default_factory=list,
        description="List of products/items in the invoice"
    )
    invoice_total: float = Field(..., description="Total invoice amount", ge=0.0)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
                    },
                    {
                        "quantity": 1,
                        "name": "Product B",
                        "unit_price": 49.99,
                        "total": 49.99
                    }
                ],
                "invoice_total": 109.97
            }
        }
    )


class InformationData(BaseModel):
    """Schema for extracted information document data."""
    
    description: str = Field(..., description="Document description")
    content_summary: str = Field(..., description="Summary of document content")
    sentiment: SentimentType = Field(..., description="Sentiment analysis result")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "A business report discussing quarterly performance",
                "content_summary": "The document covers Q4 2024 financial results, showing positive growth in revenue and market expansion.",
                "sentiment": "positive"
            }
        }
    )


class DocumentResponse(BaseModel):
    """Response schema for document upload and analysis endpoint."""
    
    document_id: int = Field(..., description="ID of the document record in database")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type (PDF, JPG, PNG)")
    s3_key: str = Field(..., description="S3 object key where file is stored")
    classification: DocumentClassification = Field(..., description="Document classification (Invoice or Information)")
    extracted_data: Union[InvoiceData, InformationData] = Field(
        ...,
        description="Extracted data based on classification"
    )
    uploaded_at: datetime = Field(..., description="Timestamp when document was uploaded")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": 1,
                "filename": "invoice_2024.pdf",
                "file_type": "PDF",
                "s3_key": "documents/2024/12/invoice_2024.pdf",
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
        }
    )

