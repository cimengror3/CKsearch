"""
CKSEARCH API - Database Models
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base
import enum


class TierEnum(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"
    ADMIN = "admin"


class User(Base):
    """User model - tracked by fingerprint."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fingerprint = Column(String(64), unique=True, nullable=False, index=True)
    tier = Column(Enum(TierEnum), default=TierEnum.FREE, nullable=False)
    
    # License
    license_key = Column(String(32), nullable=True)
    expires_at = Column(DateTime, nullable=True)  # NULL = never (for admin) or free
    
    # Usage tracking
    daily_requests = Column(Integer, default=0)
    daily_reset_at = Column(DateTime, nullable=True)
    total_requests = Column(Integer, default=0)
    
    # Referral system
    referral_code = Column(String(8), unique=True, nullable=True)
    referred_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    extra_requests = Column(Integer, default=0)  # Bonus from referrals
    
    # Status
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    last_ip = Column(String(45), nullable=True)
    
    # Device info
    device_info = Column(JSON, nullable=True)
    
    # Relationships
    telemetry = relationship("Telemetry", back_populates="user")
    

class License(Base):
    """License keys for premium users."""
    __tablename__ = "licenses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(32), unique=True, nullable=False, index=True)
    duration_days = Column(Integer, nullable=False)  # 7, 14, 30, 365
    
    # Status
    is_used = Column(Boolean, default=False)
    used_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)
    
    # Notes
    note = Column(Text, nullable=True)


class Telemetry(Base):
    """Usage telemetry for analytics."""
    __tablename__ = "telemetry"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # What was used
    module = Column(String(50), nullable=False)  # phone, email, username, etc.
    scan_mode = Column(String(20), nullable=True)  # quick, deep
    target_hash = Column(String(64), nullable=True)  # SHA256 of target (privacy)
    
    # Result
    success = Column(Boolean, default=True)
    error = Column(Text, nullable=True)
    
    # Context
    version = Column(String(20), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="telemetry")


class Setting(Base):
    """Global settings (maintenance mode, broadcast, etc.)."""
    __tablename__ = "settings"
    
    key = Column(String(50), primary_key=True)
    value = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Default settings to create
DEFAULT_SETTINGS = {
    "maintenance_mode": False,
    "maintenance_message": "Sistem sedang dalam pemeliharaan. Silakan coba lagi nanti.",
    "broadcast_message": None,
    "current_version": "1.0.0",
    "min_version": "1.0.0",
    "update_url": "https://github.com/CimenkDev/CKSEARCH/releases/latest",
}
