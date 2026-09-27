from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class DiagnosticCentreCreate(BaseModel):
    """Schema for creating a diagnostic centre."""

    name: str = Field(
        ..., min_length=2, max_length=255, description="Centre name"
    )
    address: str = Field(
        ..., min_length=5, max_length=500, description="Street address"
    )
    city: str = Field(
        ..., min_length=2, max_length=100, description="City"
    )
    state: str = Field(
        ..., min_length=2, max_length=100, description="State"
    )
    pincode: str = Field(
        ..., min_length=4, max_length=10, description="Postal code"
    )
    phone: Optional[str] = Field(
        None, max_length=20, description="Contact phone"
    )
    email: Optional[str] = Field(
        None, max_length=255, description="Contact email"
    )


class DiagnosticCentreUpdate(BaseModel):
    """Schema for updating a diagnostic centre."""

    name: Optional[str] = Field(
        None, min_length=2, max_length=255
    )
    address: Optional[str] = Field(
        None, min_length=5, max_length=500
    )
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    pincode: Optional[str] = Field(None, min_length=4, max_length=10)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class DiagnosticTestCreate(BaseModel):
    """Schema for creating a diagnostic test."""

    name: str = Field(
        ..., min_length=2, max_length=255, description="Test name"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Test description"
    )
    category: Optional[str] = Field(
        None, max_length=100, description="Test category"
    )


class DiagnosticTestResponse(BaseModel):
    """Schema for diagnostic test response."""

    id: UUID
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CentreTestCreate(BaseModel):
    """Schema for adding a test to a centre with pricing."""

    test_id: UUID = Field(..., description="ID of the diagnostic test")
    price: Decimal = Field(
        ..., gt=0, max_digits=10, decimal_places=2, description="Test price"
    )

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Price must be greater than zero")
        return v


class CentreTestResponse(BaseModel):
    """Schema for centre-test association response."""

    id: UUID
    centre_id: UUID
    test_id: UUID
    price: Decimal
    is_available: bool
    test: DiagnosticTestResponse
    created_at: datetime

    model_config = {"from_attributes": True}


class DiagnosticCentreResponse(BaseModel):
    """Schema for diagnostic centre response with available tests."""

    id: UUID
    name: str
    address: str
    city: str
    state: str
    pincode: str
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    centre_tests: List[CentreTestResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
