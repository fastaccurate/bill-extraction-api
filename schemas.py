"""
Pydantic models for request/response validation
Matches Postman collection spec exactly
"""
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional
from enum import Enum


class PageTypeEnum(str, Enum):
    """Page type classification"""
    BILL_DETAIL = "Bill Detail"
    FINAL_BILL = "Final Bill"
    PHARMACY = "Pharmacy"


class BillItem(BaseModel):
    """Individual line item in a bill"""
    item_name: str = Field(..., description="Item name as mentioned in bill")
    item_amount: float = Field(..., description="Net amount post discounts")
    item_rate: float = Field(..., description="Rate per unit")
    item_quantity: float = Field(..., description="Quantity")
    confidence: Optional[float] = Field(None, description="Extraction confidence 0-1")

    class Config:
        json_schema_extra = {
            "example": {
                "item_name": "Consultation Fee",
                "item_amount": 500.0,
                "item_rate": 500.0,
                "item_quantity": 1.0,
                "confidence": 0.95
            }
        }


class PageLineItems(BaseModel):
    """Line items for a single page"""
    page_no: str = Field(..., description="Page number")
    page_type: str = Field(
        default="Bill Detail", 
        description="Type of page: Bill Detail, Final Bill, Pharmacy"
    )
    bill_items: List[BillItem] = Field(
        default_factory=list, 
        description="List of line items on this page"
    )


class TokenUsage(BaseModel):
    """Token usage tracking (for LLM-based approaches)"""
    total_tokens: int = Field(default=0, description="Total tokens used")
    input_tokens: int = Field(default=0, description="Input tokens")
    output_tokens: int = Field(default=0, description="Output tokens")


class BillExtractionData(BaseModel):
    """Extracted bill data"""
    pagewise_line_items: List[PageLineItems] = Field(
        ..., 
        description="Line items grouped by page"
    )
    total_item_count: int = Field(
        ..., 
        description="Total count of items across all pages"
    )
    reconciled_amount: Optional[float] = Field(
        None, 
        description="Sum of all line items"
    )


class ExtractBillRequest(BaseModel):
    """Request body for /extract-bill-data endpoint"""
    document: HttpUrl = Field(
        ..., 
        description="URL of the bill document (image or PDF)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "document": "https://example.com/bill.png"
            }
        }


class ExtractBillResponse(BaseModel):
    """Response body from /extract-bill-data endpoint"""
    is_success: bool = Field(..., description="Whether extraction succeeded")
    token_usage: TokenUsage = Field(
        ..., 
        description="LLM token usage (0 for free approach)"
    )
    data: Optional[BillExtractionData] = Field(
        None, 
        description="Extracted data (null if failed)"
    )
    error: Optional[str] = Field(
        None, 
        description="Error message if failed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "is_success": True,
                "token_usage": {
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0
                },
                "data": {
                    "pagewise_line_items": [
                        {
                            "page_no": "1",
                            "page_type": "Bill Detail",
                            "bill_items": [
                                {
                                    "item_name": "Consultation",
                                    "item_amount": 500.0,
                                    "item_rate": 500.0,
                                    "item_quantity": 1.0,
                                    "confidence": 0.95
                                }
                            ]
                        }
                    ],
                    "total_item_count": 5,
                    "reconciled_amount": 2500.0
                },
                "error": None
            }
        }
