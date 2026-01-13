"""
CKSEARCH API - Admin Router
Protected endpoints untuk admin management.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import User, License, Telemetry, Setting, TierEnum
from ..schemas import (
    AdminLoginRequest, AdminLoginResponse,
    GenerateLicenseRequest, GenerateLicenseResponse,
    UserListResponse, StatsResponse,
    BanRequest, BroadcastRequest, MaintenanceRequest
)
from ..auth import verify_admin_secret, create_admin_token, verify_admin_token, generate_license_key

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(data: AdminLoginRequest):
    """Login admin dengan secret key."""
    if not verify_admin_secret(data.secret):
        return AdminLoginResponse(
            success=False,
            token=None,
            message="Invalid admin secret",
        )
    
    token = create_admin_token({"sub": "admin"})
    return AdminLoginResponse(
        success=True,
        token=token,
        message="Login successful",
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
    _: dict = Depends(verify_admin_token)
):
    """Get usage statistics."""
    total_users = db.query(func.count(User.id)).scalar()
    free_users = db.query(func.count(User.id)).filter(User.tier == TierEnum.FREE).scalar()
    premium_users = db.query(func.count(User.id)).filter(User.tier == TierEnum.PREMIUM).scalar()
    admin_users = db.query(func.count(User.id)).filter(User.tier == TierEnum.ADMIN).scalar()
    
    # Today's requests
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_requests = db.query(func.count(Telemetry.id)).filter(
        Telemetry.created_at >= today
    ).scalar()
    
    # Total requests
    total_requests = db.query(func.sum(User.total_requests)).scalar() or 0
    
    # Licenses
    active_licenses = db.query(func.count(License.id)).filter(
        License.is_used == True
    ).scalar()
    unused_licenses = db.query(func.count(License.id)).filter(
        License.is_used == False
    ).scalar()
    
    return StatsResponse(
        total_users=total_users,
        free_users=free_users,
        premium_users=premium_users,
        admin_users=admin_users,
        total_requests_today=today_requests,
        total_requests_all=total_requests,
        active_licenses=active_licenses,
        unused_licenses=unused_licenses,
    )


@router.get("/users", response_model=UserListResponse)
async def list_users(
    tier: Optional[str] = None,
    is_banned: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_admin_token)
):
    """List all users with filters."""
    query = db.query(User)
    
    if tier:
        query = query.filter(User.tier == tier)
    if is_banned is not None:
        query = query.filter(User.is_banned == is_banned)
    
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    
    user_list = []
    for u in users:
        user_list.append({
            "id": str(u.id),
            "fingerprint": u.fingerprint[:8] + "...",  # Shortened for privacy
            "tier": u.tier.value,
            "daily_requests": u.daily_requests,
            "total_requests": u.total_requests,
            "extra_requests": u.extra_requests,
            "is_banned": u.is_banned,
            "expires_at": u.expires_at.isoformat() if u.expires_at else None,
            "created_at": u.created_at.isoformat(),
            "last_seen": u.last_seen.isoformat() if u.last_seen else None,
            "last_ip": u.last_ip,
            "referral_code": u.referral_code,
        })
    
    return UserListResponse(total=total, users=user_list)


@router.get("/user/{user_id}")
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_admin_token)
):
    """Get user details."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user.id),
        "fingerprint": user.fingerprint,
        "tier": user.tier.value,
        "license_key": user.license_key,
        "daily_requests": user.daily_requests,
        "total_requests": user.total_requests,
        "extra_requests": user.extra_requests,
        "is_banned": user.is_banned,
        "ban_reason": user.ban_reason,
        "expires_at": user.expires_at.isoformat() if user.expires_at else None,
        "created_at": user.created_at.isoformat(),
        "last_seen": user.last_seen.isoformat() if user.last_seen else None,
        "last_ip": user.last_ip,
        "referral_code": user.referral_code,
        "device_info": user.device_info,
    }


@router.post("/user/{user_id}/ban")
async def ban_user(
    user_id: str,
    data: BanRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_admin_token)
):
    """Ban a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_banned = True
    user.ban_reason = data.reason
    db.commit()
    
    return {"success": True, "message": f"User {user_id} has been banned"}


@router.post("/user/{user_id}/unban")
async def unban_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_admin_token)
):
    """Unban a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_banned = False
    user.ban_reason = None
    db.commit()
    
    return {"success": True, "message": f"User {user_id} has been unbanned"}


@router.post("/user/{user_id}/set-tier")
async def set_user_tier(
    user_id: str,
    tier: str,
    days: Optional[int] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_admin_token)
):
    """Set user tier (admin can promote to any tier)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if tier not in ["free", "premium", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid tier")
    
    user.tier = TierEnum(tier)
    
    if tier == "premium" and days:
        user.expires_at = datetime.utcnow() + timedelta(days=days)
    elif tier == "admin":
        user.expires_at = None  # Admin never expires
    elif tier == "free":
        user.expires_at = None
        user.license_key = None
    
    db.commit()
    
    return {"success": True, "message": f"User tier set to {tier}"}


@router.post("/user/{user_id}/reset-device")
async def reset_device_binding(
    user_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_admin_token)
):
    """Reset device binding (allow user to re-bind license to new device)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate new fingerprint placeholder (user will need to re-validate)
    old_fingerprint = user.fingerprint
    user.fingerprint = f"RESET_{user.fingerprint[:32]}"
    db.commit()
    
    return {
        "success": True,
        "message": "Device binding reset. User can now activate from new device.",
        "old_fingerprint": old_fingerprint[:8] + "...",
    }


@router.post("/license/generate", response_model=GenerateLicenseResponse)
async def generate_licenses(
    data: GenerateLicenseRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_admin_token)
):
    """Generate new license keys."""
    licenses = []
    
    for _ in range(data.count):
        key = generate_license_key()
        
        # Ensure unique
        while db.query(License).filter(License.key == key).first():
            key = generate_license_key()
        
        license_obj = License(
            key=key,
            duration_days=data.duration_days,
            note=data.note,
        )
        db.add(license_obj)
        licenses.append(key)
    
    db.commit()
    
    return GenerateLicenseResponse(
        success=True,
        licenses=licenses,
    )


@router.get("/licenses")
async def list_licenses(
    is_used: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_admin_token)
):
    """List all licenses."""
    query = db.query(License)
    
    if is_used is not None:
        query = query.filter(License.is_used == is_used)
    
    licenses = query.order_by(License.created_at.desc()).limit(limit).all()
    
    return {
        "total": query.count(),
        "licenses": [
            {
                "id": str(lic.id),
                "key": lic.key,
                "duration_days": lic.duration_days,
                "is_used": lic.is_used,
                "used_by": str(lic.used_by) if lic.used_by else None,
                "created_at": lic.created_at.isoformat(),
                "activated_at": lic.activated_at.isoformat() if lic.activated_at else None,
                "note": lic.note,
            }
            for lic in licenses
        ]
    }


@router.post("/broadcast")
async def set_broadcast(
    data: BroadcastRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_admin_token)
):
    """Set broadcast message for all users."""
    setting = db.query(Setting).filter(Setting.key == "broadcast_message").first()
    if setting:
        setting.value = data.message
    else:
        db.add(Setting(key="broadcast_message", value=data.message))
    
    db.commit()
    
    return {"success": True, "message": "Broadcast message updated"}


@router.post("/maintenance")
async def set_maintenance(
    data: MaintenanceRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_admin_token)
):
    """Set maintenance mode."""
    # Update maintenance_mode
    mode_setting = db.query(Setting).filter(Setting.key == "maintenance_mode").first()
    if mode_setting:
        mode_setting.value = data.enabled
    else:
        db.add(Setting(key="maintenance_mode", value=data.enabled))
    
    # Update message if provided
    if data.message:
        msg_setting = db.query(Setting).filter(Setting.key == "maintenance_message").first()
        if msg_setting:
            msg_setting.value = data.message
        else:
            db.add(Setting(key="maintenance_message", value=data.message))
    
    db.commit()
    
    return {"success": True, "message": f"Maintenance mode {'enabled' if data.enabled else 'disabled'}"}


@router.post("/settings/{key}")
async def update_setting(
    key: str,
    value: dict,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_admin_token)
):
    """Update any setting."""
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting:
        setting.value = value.get("value")
    else:
        db.add(Setting(key=key, value=value.get("value")))
    
    db.commit()
    
    return {"success": True, "message": f"Setting {key} updated"}
