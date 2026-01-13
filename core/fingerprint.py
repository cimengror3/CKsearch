"""
CKSEARCH - Device Fingerprint Generator
=========================================
Generate unique device fingerprint for license binding.
"""

import hashlib
import platform
import uuid
import os
import socket
from typing import Dict, Any


def get_mac_address() -> str:
    """Get MAC address of primary network interface."""
    try:
        mac = uuid.getnode()
        mac_str = ':'.join(('%012x' % mac)[i:i+2] for i in range(0, 12, 2))
        return mac_str
    except:
        return "00:00:00:00:00:00"


def get_cpu_id() -> str:
    """Get CPU identifier."""
    try:
        if platform.system() == "Linux":
            # Try to get CPU info from /proc/cpuinfo
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "Serial" in line or "model name" in line:
                            return line.split(":")[1].strip()[:32]
            except:
                pass
        
        # Fallback: use processor info
        return platform.processor()[:32] or "unknown_cpu"
    except:
        return "unknown_cpu"


def get_hostname() -> str:
    """Get system hostname."""
    try:
        return socket.gethostname()
    except:
        return "unknown_host"


def get_os_username() -> str:
    """Get OS username."""
    try:
        return os.getenv("USER") or os.getenv("USERNAME") or "unknown_user"
    except:
        return "unknown_user"


def get_machine_id() -> str:
    """Get machine ID (Linux only)."""
    try:
        if platform.system() == "Linux":
            paths = [
                "/etc/machine-id",
                "/var/lib/dbus/machine-id",
            ]
            for path in paths:
                if os.path.exists(path):
                    with open(path, "r") as f:
                        return f.read().strip()
    except:
        pass
    return ""


def get_device_info() -> Dict[str, Any]:
    """Get detailed device info for telemetry."""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": get_hostname(),
        "python_version": platform.python_version(),
    }


def generate_fingerprint() -> str:
    """
    Generate unique device fingerprint.
    
    Combines: MAC Address + CPU ID + Hostname + OS Username + Machine ID
    Returns: SHA256 hash (64 chars)
    """
    components = [
        get_mac_address(),
        get_cpu_id(),
        get_hostname(),
        get_os_username(),
        get_machine_id(),
        platform.system(),
        platform.node(),
    ]
    
    # Combine all components
    combined = "|".join(str(c) for c in components if c)
    
    # Generate SHA256 hash
    fingerprint = hashlib.sha256(combined.encode()).hexdigest()
    
    return fingerprint


def get_fingerprint_short() -> str:
    """Get shortened fingerprint for display (8 chars)."""
    return generate_fingerprint()[:8]


# Cache fingerprint to avoid regeneration
_cached_fingerprint = None


def get_fingerprint() -> str:
    """Get cached fingerprint."""
    global _cached_fingerprint
    if _cached_fingerprint is None:
        _cached_fingerprint = generate_fingerprint()
    return _cached_fingerprint


if __name__ == "__main__":
    # Test fingerprint generation
    print("Device Fingerprint Generator")
    print("=" * 50)
    print(f"MAC Address:  {get_mac_address()}")
    print(f"CPU ID:       {get_cpu_id()}")
    print(f"Hostname:     {get_hostname()}")
    print(f"Username:     {get_os_username()}")
    print(f"Machine ID:   {get_machine_id()[:16]}...")
    print("=" * 50)
    print(f"Fingerprint:  {generate_fingerprint()}")
    print(f"Short:        {get_fingerprint_short()}")
