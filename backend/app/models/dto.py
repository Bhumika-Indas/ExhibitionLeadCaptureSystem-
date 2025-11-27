"""
Data Transfer Objects (DTOs) for API requests and responses
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ============================================================
# AUTH DTOs
# ============================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    employee_id: int
    full_name: str


# ============================================================
# LEAD DTOs
# ============================================================

class LeadCreateRequest(BaseModel):
    exhibition_id: int
    source_code: str = "employee_scan"
    company_name: Optional[str] = None
    primary_visitor_name: Optional[str] = None
    primary_visitor_designation: Optional[str] = None
    primary_visitor_phone: Optional[str] = None
    primary_visitor_email: Optional[EmailStr] = None
    discussion_summary: Optional[str] = None
    next_step: Optional[str] = None


class LeadUpdateRequest(BaseModel):
    company_name: Optional[str] = None
    primary_visitor_name: Optional[str] = None
    primary_visitor_designation: Optional[str] = None
    primary_visitor_phone: Optional[str] = None
    primary_visitor_email: Optional[EmailStr] = None
    discussion_summary: Optional[str] = None
    next_step: Optional[str] = None
    status_code: Optional[str] = None


class LeadResponse(BaseModel):
    lead_id: int
    exhibition_id: int
    source_code: str
    company_name: Optional[str]
    primary_visitor_name: Optional[str]
    primary_visitor_phone: Optional[str]
    status_code: str
    whatsapp_confirmed: Optional[bool]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# EXTRACTION DTOs
# ============================================================

class CardExtractionResponse(BaseModel):
    success: bool
    lead_id: Optional[int] = None
    extraction_result: Optional[dict] = None
    error: Optional[str] = None


class VoiceExtractionResponse(BaseModel):
    success: bool
    transcript: Optional[str] = None
    summary: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    error: Optional[str] = None


# ============================================================
# MESSAGE DTOs
# ============================================================

class MessageResponse(BaseModel):
    message_id: int
    lead_id: int
    sender_type: str
    message_text: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# WHATSAPP DTOs
# ============================================================

class WhatsAppWebhookRequest(BaseModel):
    """Generic webhook structure"""
    object: Optional[str] = None
    entry: Optional[List[dict]] = None


class WhatsAppSendRequest(BaseModel):
    to: str
    message: str


# ============================================================
# ANALYTICS DTOs
# ============================================================

class AnalyticsSummaryResponse(BaseModel):
    total_leads: int
    confirmed_leads: int
    pending_leads: int
    employee_scan_count: int
    qr_whatsapp_count: int
    confirmation_rate: float
