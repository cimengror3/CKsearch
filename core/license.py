"""
CKSEARCH - License Client
===========================
Client untuk komunikasi dengan API server untuk validasi lisensi.
"""

import requests
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

import config
from core.fingerprint import get_fingerprint, get_device_info


# API Configuration
API_BASE_URL = "https://api.cimeng.web.id"  # Production
# API_BASE_URL = "http://localhost:8000"  # Development

TIMEOUT = 10  # seconds


@dataclass
class LicenseInfo:
    """License information from API."""
    success: bool
    tier: str  # free, premium, admin
    remaining_requests: int
    daily_limit: int
    extra_requests: int
    expires_at: Optional[datetime]
    is_banned: bool
    ban_reason: Optional[str]
    broadcast_message: Optional[str]
    maintenance_mode: bool
    maintenance_message: Optional[str]
    update_available: bool
    update_url: Optional[str]
    referral_code: Optional[str]
    reset_at: Optional[datetime]
    contact_info: str
    error: Optional[str] = None


class LicenseClient:
    """Client untuk komunikasi dengan license server."""
    
    def __init__(self):
        self.fingerprint = get_fingerprint()
        self.device_info = get_device_info()
        self._cached_license: Optional[LicenseInfo] = None
    
    def validate(self) -> LicenseInfo:
        """
        Validate fingerprint dengan server.
        Returns LicenseInfo dengan tier dan limit info.
        """
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/v1/validate",
                json={
                    "fingerprint": self.fingerprint,
                    "version": config.VERSION,
                    "device_info": self.device_info,
                },
                timeout=TIMEOUT,
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse expires_at
                expires_at = None
                if data.get("expires_at"):
                    try:
                        expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
                    except:
                        pass
                
                # Parse reset_at
                reset_at = None
                if data.get("reset_at"):
                    try:
                        reset_at = datetime.fromisoformat(data["reset_at"].replace("Z", "+00:00"))
                    except:
                        pass
                
                self._cached_license = LicenseInfo(
                    success=data.get("success", False),
                    tier=data.get("tier", "free"),
                    remaining_requests=data.get("remaining_requests", 0),
                    daily_limit=data.get("daily_limit", 5),
                    extra_requests=data.get("extra_requests", 0),
                    expires_at=expires_at,
                    is_banned=data.get("is_banned", False),
                    ban_reason=data.get("ban_reason"),
                    broadcast_message=data.get("broadcast_message"),
                    maintenance_mode=data.get("maintenance_mode", False),
                    maintenance_message=data.get("maintenance_message"),
                    update_available=data.get("update_available", False),
                    update_url=data.get("update_url"),
                    referral_code=data.get("referral_code"),
                    reset_at=reset_at,
                    contact_info=data.get("contact_info", "@cimenk"),
                )
                return self._cached_license
            else:
                return self._offline_fallback(f"API Error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            return self._offline_fallback("Cannot connect to license server")
        except requests.exceptions.Timeout:
            return self._offline_fallback("Connection timeout")
        except Exception as e:
            return self._offline_fallback(str(e))
    
    def _offline_fallback(self, error: str) -> LicenseInfo:
        """Return offline fallback when API is unreachable."""
        # If we have cached license, use it (grace period)
        if self._cached_license:
            self._cached_license.error = f"Offline mode: {error}"
            return self._cached_license
        
        # No cache, allow limited offline usage
        return LicenseInfo(
            success=False,
            tier="free",
            remaining_requests=3,  # Limited offline
            daily_limit=3,
            extra_requests=0,
            expires_at=None,
            is_banned=False,
            ban_reason=None,
            broadcast_message=None,
            maintenance_mode=False,
            maintenance_message=None,
            update_available=False,
            update_url=None,
            referral_code=None,
            reset_at=None,
            contact_info="@cimenk",
            error=error,
        )
    
    def activate(self, license_key: str) -> Dict[str, Any]:
        """Activate a license key."""
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/v1/activate",
                json={
                    "fingerprint": self.fingerprint,
                    "license_key": license_key,
                },
                timeout=TIMEOUT,
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "message": f"Error: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"Connection error: {str(e)}"}
    
    def log_telemetry(self, module: str, scan_mode: str = None, target: str = None, 
                      success: bool = True, error: str = None) -> Dict[str, Any]:
        """Log usage telemetry to server."""
        try:
            # Hash target for privacy
            target_hash = None
            if target:
                target_hash = hashlib.sha256(target.encode()).hexdigest()
            
            response = requests.post(
                f"{API_BASE_URL}/api/v1/telemetry",
                json={
                    "fingerprint": self.fingerprint,
                    "module": module,
                    "scan_mode": scan_mode,
                    "target_hash": target_hash,
                    "success": success,
                    "error": error,
                    "version": config.VERSION,
                },
                timeout=TIMEOUT,
            )
            
            if response.status_code == 200:
                return response.json()
            return {"success": False}
            
        except:
            return {"success": False}
    
    def use_referral(self, referral_code: str) -> Dict[str, Any]:
        """Use a referral code to get bonus requests."""
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/v1/referral",
                json={
                    "fingerprint": self.fingerprint,
                    "referral_code": referral_code,
                },
                timeout=TIMEOUT,
            )
            
            if response.status_code == 200:
                return response.json()
            return {"success": False, "message": f"Error: {response.status_code}"}
            
        except Exception as e:
            return {"success": False, "message": f"Connection error: {str(e)}"}
    
    def check_version(self) -> Dict[str, Any]:
        """Check for updates."""
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/v1/version",
                timeout=TIMEOUT,
            )
            
            if response.status_code == 200:
                return response.json()
            return {"update_available": False}
            
        except:
            return {"update_available": False}
    
    @property
    def is_premium(self) -> bool:
        """Check if current user is premium."""
        if self._cached_license:
            return self._cached_license.tier in ["premium", "admin"]
        return False
    
    @property
    def is_admin(self) -> bool:
        """Check if current user is admin."""
        if self._cached_license:
            return self._cached_license.tier == "admin"
        return False
    
    @property
    def can_use(self) -> bool:
        """Check if user can make requests."""
        if self._cached_license:
            if self._cached_license.is_banned:
                return False
            if self._cached_license.maintenance_mode:
                return False
            if self._cached_license.tier in ["premium", "admin"]:
                return True
            return self._cached_license.remaining_requests > 0
        return False


# Global instance
_license_client: Optional[LicenseClient] = None


def get_license_client() -> LicenseClient:
    """Get global license client instance."""
    global _license_client
    if _license_client is None:
        _license_client = LicenseClient()
    return _license_client


def validate_license() -> LicenseInfo:
    """Shortcut to validate license."""
    return get_license_client().validate()


def log_usage(module: str, **kwargs) -> Dict[str, Any]:
    """Shortcut to log usage."""
    return get_license_client().log_telemetry(module, **kwargs)
