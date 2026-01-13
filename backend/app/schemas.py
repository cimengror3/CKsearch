"""
CKSEARCH API - Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


# Enums
class TierEnum(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    ADMIN = "admin"


# === Request Schemas ===

class ValidateRequest(BaseModel):
    """Request untuk validasi fingerprint."""
    fingerprint: str = Field(..., min_length=32, max_length=64)
    version: Optional[str] = None
    device_info: Optional[dict] = None


class ActivateRequest(BaseModel):
    """Request untuk aktivasi license."""
    fingerprint: str = Field(..., min_length=32, max_length=64)
    license_key: str = Field(..., min_length=16, max_length=32)


class TelemetryRequest(BaseModel):
    """Request untuk log telemetry."""
    fingerprint: str
    module: str
    scan_mode: Optional[str] = None
    target_hash: Optional[str] = None
    success: bool = True
    error: Optional[str] = None
    version: Optional[str] = None


class ReferralRequest(BaseModel):
    """Request untuk referral."""
    fingerprint: str
    referral_code: str


# === Response Schemas ===

class ValidateResponse(BaseModel):
    """Response dari validasi."""
    success: bool
    tier: TierEnum
    fingerprint: str
    
    # Limits
    remaining_requests: int
    daily_limit: int
    extra_requests: int
    
    # Status
    expires_at: Optional[datetime] = None
    is_banned: bool = False
    ban_reason: Optional[str] = None
    
    # Messages
    broadcast_message: Optional[str] = None
    maintenance_mode: bool = False
    maintenance_message: Optional[str] = None
    
    # Version
    current_version: str
    update_available: bool = False
    update_url: Optional[str] = None
    
    # Referral
    referral_code: Optional[str] = None
    
    # Reset time
    reset_at: Optional[datetime] = None
    
    # Contact
    contact_info: str


class ActivateResponse(BaseModel):
    """Response dari aktivasi license."""
    success: bool
    message: str
    tier: Optional[TierEnum] = None
    expires_at: Optional[datetime] = None


class TelemetryResponse(BaseModel):
    """Response dari log telemetry."""
    success: bool
    remaining_requests: int


class VersionResponse(BaseModel):
    """Response dari version check."""
    current_version: str
    min_version: str
    update_available: bool
    update_url: Optional[str] = None
    maintenance_mode: bool = False


class ReferralResponse(BaseModel):
    """Response dari referral."""
    success: bool
    message: str
    extra_requests: int


# === Admin Schemas ===

class AdminLoginRequest(BaseModel):
    """Admin login request."""
    secret: str


class AdminLoginResponse(BaseModel):
    """Admin login response."""
    success: bool
    token: Optional[str] = None
    message: str


class GenerateLicenseRequest(BaseModel):
    """Generate license request."""
    duration_days: int = Field(..., ge=1, le=365)
    count: int = Field(1, ge=1, le=100)
    note: Optional[str] = None


class GenerateLicenseResponse(BaseModel):
    """Generate license response."""
    success: bool
    licenses: List[str]


class UserListResponse(BaseModel):
    """User list for admin."""
    total: int
    users: List[dict]


class StatsResponse(BaseModel):
    """Statistics for admin."""
    total_users: int
    free_users: int
    premium_users: int
    admin_users: int
    total_requests_today: int
    total_requests_all: int
    active_licenses: int
    unused_licenses: int


class BanRequest(BaseModel):
    """Ban user request."""
    reason: Optional[str] = None


class BroadcastRequest(BaseModel):
    """Set broadcast message."""
    message: Optional[str] = None


class MaintenanceRequest(BaseModel):
    """Set maintenance mode."""
    enabled: bool
    message: Optional[str] = None
