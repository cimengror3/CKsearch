"""
CKSEARCH API - License Router
Public endpoints untuk validasi dan aktivasi license.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import User, License, Setting, TierEnum, DEFAULT_SETTINGS
from ..schemas import (
    ValidateRequest, ValidateResponse,
    ActivateRequest, ActivateResponse,
    TelemetryRequest, TelemetryResponse,
    VersionResponse, ReferralRequest, ReferralResponse
)
from ..config import settings
from ..auth import generate_referral_code

router = APIRouter(prefix="/api/v1", tags=["License"])


def get_client_ip(request: Request) -> str:
    """Get client IP address."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_setting(db: Session, key: str):
    """Get setting value from database."""
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting:
        return setting.value
    return DEFAULT_SETTINGS.get(key)


def ensure_settings(db: Session):
    """Ensure default settings exist."""
    for key, value in DEFAULT_SETTINGS.items():
        existing = db.query(Setting).filter(Setting.key == key).first()
        if not existing:
            db.add(Setting(key=key, value=value))
    db.commit()


@router.post("/validate", response_model=ValidateResponse)
async def validate_fingerprint(
    request: Request,
    data: ValidateRequest,
    db: Session = Depends(get_db)
):
    """
    Validate fingerprint dan return tier info.
    Auto-create user jika belum ada (free tier).
    """
    ensure_settings(db)
    client_ip = get_client_ip(request)
    
    # Check maintenance mode
    maintenance = get_setting(db, "maintenance_mode")
    maintenance_msg = get_setting(db, "maintenance_message")
    
    # Find or create user
    user = db.query(User).filter(User.fingerprint == data.fingerprint).first()
    
    if not user:
        # Auto-create free user
        user = User(
            fingerprint=data.fingerprint,
            tier=TierEnum.FREE,
            referral_code=generate_referral_code(),
            device_info=data.device_info,
            last_ip=client_ip,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update last seen
        user.last_seen = datetime.utcnow()
        user.last_ip = client_ip
        if data.device_info:
            user.device_info = data.device_info
        db.commit()
    
    # Check if banned
    if user.is_banned:
        return ValidateResponse(
            success=False,
            tier=user.tier,
            fingerprint=data.fingerprint,
            remaining_requests=0,
            daily_limit=0,
            extra_requests=0,
            is_banned=True,
            ban_reason=user.ban_reason,
            current_version=get_setting(db, "current_version") or settings.current_version,
            contact_info=settings.contact_info,
        )
    
    # Check premium expiry
    if user.tier == TierEnum.PREMIUM and user.expires_at:
        if user.expires_at < datetime.utcnow():
            # Premium expired, revert to free
            user.tier = TierEnum.FREE
            user.license_key = None
            user.expires_at = None
            db.commit()
    
    # Calculate remaining requests
    daily_limit = 0 if user.tier in [TierEnum.PREMIUM, TierEnum.ADMIN] else settings.free_daily_limit
    
    # Reset daily counter if new day (WIB = UTC+7)
    now_utc = datetime.utcnow()
    wib_offset = timedelta(hours=7)
    now_wib = now_utc + wib_offset
    today_wib = now_wib.replace(hour=0, minute=0, second=0, microsecond=0)
    today_reset = today_wib - wib_offset  # Convert back to UTC
    
    if user.daily_reset_at is None or user.daily_reset_at < today_reset:
        user.daily_requests = 0
        user.daily_reset_at = today_reset
        db.commit()
    
    # Calculate remaining
    if user.tier in [TierEnum.PREMIUM, TierEnum.ADMIN]:
        remaining = 999999  # Unlimited
    else:
        remaining = max(0, daily_limit + user.extra_requests - user.daily_requests)
    
    # Next reset time (tomorrow 00:00 WIB)
    tomorrow_wib = today_wib + timedelta(days=1)
    reset_at = tomorrow_wib - wib_offset  # UTC
    
    # Version check
    current_v = get_setting(db, "current_version") or settings.current_version
    min_v = get_setting(db, "min_version") or settings.current_version
    update_available = data.version and data.version < current_v
    
    return ValidateResponse(
        success=True,
        tier=user.tier,
        fingerprint=data.fingerprint,
        remaining_requests=remaining,
        daily_limit=daily_limit,
        extra_requests=user.extra_requests,
        expires_at=user.expires_at,
        is_banned=False,
        broadcast_message=get_setting(db, "broadcast_message"),
        maintenance_mode=maintenance,
        maintenance_message=maintenance_msg if maintenance else None,
        current_version=current_v,
        update_available=update_available,
        update_url=get_setting(db, "update_url") if update_available else None,
        referral_code=user.referral_code,
        reset_at=reset_at,
        contact_info=settings.contact_info,
    )


@router.post("/activate", response_model=ActivateResponse)
async def activate_license(
    data: ActivateRequest,
    db: Session = Depends(get_db)
):
    """Activate a license key."""
    # Find user
    user = db.query(User).filter(User.fingerprint == data.fingerprint).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please validate first.")
    
    if user.is_banned:
        raise HTTPException(status_code=403, detail="User is banned.")
    
    # Clean license key
    license_key = data.license_key.upper().replace(" ", "")
    
    # Find license
    license_obj = db.query(License).filter(License.key == license_key).first()
    if not license_obj:
        return ActivateResponse(
            success=False,
            message="License key tidak valid. Silakan periksa kembali.",
        )
    
    if license_obj.is_used:
        return ActivateResponse(
            success=False,
            message="License key sudah digunakan.",
        )
    
    # Activate license
    now = datetime.utcnow()
    expires_at = now + timedelta(days=license_obj.duration_days)
    
    # If user already premium, extend expiry
    if user.tier == TierEnum.PREMIUM and user.expires_at and user.expires_at > now:
        expires_at = user.expires_at + timedelta(days=license_obj.duration_days)
    
    user.tier = TierEnum.PREMIUM
    user.license_key = license_key
    user.expires_at = expires_at
    
    license_obj.is_used = True
    license_obj.used_by = user.id
    license_obj.activated_at = now
    
    db.commit()
    
    return ActivateResponse(
        success=True,
        message=f"License berhasil diaktifkan! Premium aktif hingga {expires_at.strftime('%Y-%m-%d %H:%M')} WIB",
        tier=TierEnum.PREMIUM,
        expires_at=expires_at,
    )


@router.post("/telemetry", response_model=TelemetryResponse)
async def log_telemetry(
    request: Request,
    data: TelemetryRequest,
    db: Session = Depends(get_db)
):
    """Log usage telemetry and decrement counter."""
    from ..models import Telemetry
    
    user = db.query(User).filter(User.fingerprint == data.fingerprint).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Add telemetry record
    telem = Telemetry(
        user_id=user.id,
        module=data.module,
        scan_mode=data.scan_mode,
        target_hash=data.target_hash,
        success=data.success,
        error=data.error,
        version=data.version,
        ip_address=get_client_ip(request),
    )
    db.add(telem)
    
    # Increment counters
    user.daily_requests += 1
    user.total_requests += 1
    
    db.commit()
    
    # Calculate remaining
    if user.tier in [TierEnum.PREMIUM, TierEnum.ADMIN]:
        remaining = 999999
    else:
        remaining = max(0, settings.free_daily_limit + user.extra_requests - user.daily_requests)
    
    return TelemetryResponse(
        success=True,
        remaining_requests=remaining,
    )


@router.get("/version", response_model=VersionResponse)
async def check_version(db: Session = Depends(get_db)):
    """Check current version and update info."""
    ensure_settings(db)
    
    return VersionResponse(
        current_version=get_setting(db, "current_version") or settings.current_version,
        min_version=get_setting(db, "min_version") or settings.current_version,
        update_available=False,
        update_url=get_setting(db, "update_url"),
        maintenance_mode=get_setting(db, "maintenance_mode") or False,
    )


@router.post("/referral", response_model=ReferralResponse)
async def use_referral(
    data: ReferralRequest,
    db: Session = Depends(get_db)
):
    """Apply referral code to get bonus requests."""
    # Find user
    user = db.query(User).filter(User.fingerprint == data.fingerprint).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already referred
    if user.referred_by:
        return ReferralResponse(
            success=False,
            message="Anda sudah menggunakan kode referral.",
            extra_requests=user.extra_requests,
        )
    
    # Find referrer
    referrer = db.query(User).filter(User.referral_code == data.referral_code.upper()).first()
    if not referrer:
        return ReferralResponse(
            success=False,
            message="Kode referral tidak valid.",
            extra_requests=user.extra_requests,
        )
    
    # Prevent self-referral
    if referrer.id == user.id:
        return ReferralResponse(
            success=False,
            message="Tidak bisa menggunakan kode referral sendiri.",
            extra_requests=user.extra_requests,
        )
    
    # Apply referral (both get +1 extra request)
    user.referred_by = referrer.id
    user.extra_requests += 1
    referrer.extra_requests += 1
    
    db.commit()
    
    return ReferralResponse(
        success=True,
        message="Kode referral berhasil! Anda mendapat +1 extra request per hari.",
        extra_requests=user.extra_requests,
    )
