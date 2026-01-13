"""
CKSEARCH - Configuration Module
================================
Konfigurasi API keys, settings, dan preferences.
"""

import os
from pathlib import Path

# =============================================================================
# PROJECT INFO
# =============================================================================
PROJECT_NAME = "CKSEARCH"
VERSION = "1.0.0"
AUTHOR = "CimenkDev"
GITHUB_URL = "https://github.com/CimenkDev/CKSEARCH"

# =============================================================================
# API KEYS
# =============================================================================
API_KEYS = {
    # Numverify - Phone number validation
    "numverify": os.environ.get("NUMVERIFY_API_KEY", "d7635b301c14d53c9d421a182c4f3b9a"),
    
    # IPInfo - IP geolocation
    "ipinfo": os.environ.get("IPINFO_API_KEY", "8b08a0a91ed089"),
    
    # VirusTotal - Malware/Reputation check
    "virustotal": os.environ.get("VIRUSTOTAL_API_KEY", "eec85d551cb02384786e8453d6cecd269acd9bb6ce0386676fd83f8a071432c8"),
    
    # XposedOrNot - Email breach check (gratis, tidak perlu key)
    "xposedornot": None,
}

# =============================================================================
# DIRECTORIES
# =============================================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATES_DIR = BASE_DIR / "templates"
CACHE_DIR = BASE_DIR / ".cache"

# Create directories if not exist
for directory in [DATA_DIR, OUTPUT_DIR, TEMPLATES_DIR, CACHE_DIR]:
    directory.mkdir(exist_ok=True)

# =============================================================================
# NETWORK SETTINGS
# =============================================================================
REQUEST_TIMEOUT = 15  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
MAX_CONCURRENT_REQUESTS = 50  # untuk async

# Rate limiting (requests per second)
RATE_LIMITS = {
    "default": 5,
    "numverify": 1,
    "ipinfo": 10,
    "xposedornot": 1,
}

# =============================================================================
# PROXY SETTINGS
# =============================================================================
PROXY_ENABLED = False
PROXY_URL = None  # e.g., "socks5://127.0.0.1:9050" for Tor

# Tor configuration
TOR_ENABLED = False
TOR_SOCKS_PORT = 9050
TOR_CONTROL_PORT = 9051

# =============================================================================
# USER AGENT
# =============================================================================
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# =============================================================================
# OUTPUT SETTINGS
# =============================================================================
OUTPUT_FORMATS = ["json", "txt", "html", "csv"]
DEFAULT_OUTPUT_FORMAT = "json"
COLORIZE_OUTPUT = True

# =============================================================================
# SCANNER SETTINGS
# =============================================================================
# Port scanner
COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445,
    993, 995, 1723, 3306, 3389, 5432, 5900, 8080, 8443
]

# Username search - platforms per batch
USERNAME_BATCH_SIZE = 100

# =============================================================================
# LANGUAGE SETTINGS
# =============================================================================
DEFAULT_LANGUAGE = "id"  # 'id' for Indonesian, 'en' for English
SUPPORTED_LANGUAGES = ["id", "en"]

# =============================================================================
# LOGGING
# =============================================================================
LOG_LEVEL = "INFO"
LOG_TO_FILE = False
LOG_FILE = BASE_DIR / "cksearch.log"

# =============================================================================
# CACHE SETTINGS
# =============================================================================
CACHE_ENABLED = True
CACHE_TTL = 3600  # 1 hour in seconds
