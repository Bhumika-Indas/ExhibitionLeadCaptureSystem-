"""
Pydantic schemas for extraction module outputs
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PersonInfo(BaseModel):
    """Person information from visiting card"""
    name: Optional[str] = None
    designation: Optional[str] = None
    phones: List[str] = Field(default_factory=list)
    emails: List[str] = Field(default_factory=list)
    is_primary: bool = False


class AddressInfo(BaseModel):
    """Address information"""
    address_type: Optional[str] = Field(None, description="Factory, Corporate, Branch, etc.")
    address: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pin_code: Optional[str] = None


class BrandInfo(BaseModel):
    """Brand/Supplier information for dealer cards"""
    brand_name: str
    relationship: Optional[str] = Field(None, description="Dealer, Distributor, Authorized, Stockist")


class CardExtractionResult(BaseModel):
    """Result of visiting card extraction"""
    # Primary company (the main business on the card)
    company_name: Optional[str] = None

    # Associated brands (for dealer/distributor cards)
    brands: List[BrandInfo] = Field(default_factory=list, description="Brands/Suppliers they deal with")

    # People on the card
    persons: List[PersonInfo] = Field(default_factory=list)

    # Contact details (general, not tied to specific person)
    phones: List[str] = Field(default_factory=list, description="All phone numbers")
    emails: List[str] = Field(default_factory=list)
    websites: List[str] = Field(default_factory=list)

    # Location
    addresses: List[AddressInfo] = Field(default_factory=list)

    # Business info
    services: List[str] = Field(default_factory=list, description="Products/Services offered")
    business_type: Optional[str] = Field(None, description="Manufacturer, Dealer, Distributor, Wholesaler, Retailer")

    # Card metadata
    is_two_sided: bool = False
    back_side_type: Optional[str] = Field(None, description="Info | Decorative | Products | Mixed")
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    raw_front_text: Optional[str] = None
    raw_back_text: Optional[str] = None


class VoiceExtractionResult(BaseModel):
    """Result of voice transcription and summarization"""
    transcript: str
    summary: str
    topics: List[str] = Field(default_factory=list)
    next_step: Optional[str] = Field(None, description="Identified next action from the conversation")
    segment: Optional[str] = Field(None, description="Lead segment: decision_maker, influencer, researcher, general")
    priority: Optional[str] = Field(None, description="Priority: high, medium, low")
    interest_level: Optional[str] = Field(None, description="hot, warm, cold")
    confidence: float = Field(0.0, ge=0.0, le=1.0)
