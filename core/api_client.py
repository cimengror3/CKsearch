"""
CKSEARCH - API Client Module
=============================
Base API client dengan rate limiting, retry, dan error handling.
"""

import time
import asyncio
import aiohttp
import requests
from typing import Optional, Dict, Any, List
from functools import wraps
from rich.console import Console

import config

console = Console()


class RateLimiter:
    """Rate limiter untuk API requests."""
    
    def __init__(self, requests_per_second: float = 5.0):
        self.rate = requests_per_second
        self.last_request = 0.0
        self._lock = None
    
    def wait(self) -> None:
        """Wait untuk synchronous requests."""
        now = time.time()
        elapsed = now - self.last_request
        wait_time = (1.0 / self.rate) - elapsed
        
        if wait_time > 0:
            time.sleep(wait_time)
        
        self.last_request = time.time()
    
    async def async_wait(self) -> None:
        """Wait untuk async requests."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_request
            wait_time = (1.0 / self.rate) - elapsed
            
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            
            self.last_request = time.time()


class APIClient:
    """Base API client dengan fitur lengkap."""
    
    def __init__(
        self,
        base_url: str = "",
        api_key: Optional[str] = None,
        rate_limit: float = 5.0,
        timeout: int = None,
        headers: Dict[str, str] = None,
    ):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL untuk API
            api_key: API key (optional)
            rate_limit: Requests per second
            timeout: Request timeout in seconds
            headers: Custom headers
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout or config.REQUEST_TIMEOUT
        self.max_retries = config.MAX_RETRIES
        self.retry_delay = config.RETRY_DELAY
        
        self.rate_limiter = RateLimiter(rate_limit)
        
        # Default headers
        self.headers = {
            "User-Agent": config.DEFAULT_USER_AGENT,
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if headers:
            self.headers.update(headers)
        
        # Session untuk connection pooling
        self._session = None
        self._async_session = None
    
    @property
    def session(self) -> requests.Session:
        """Get or create requests session."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update(self.headers)
            
            # Proxy setup
            if config.PROXY_ENABLED and config.PROXY_URL:
                self._session.proxies = {
                    "http": config.PROXY_URL,
                    "https": config.PROXY_URL,
                }
        
        return self._session
    
    async def get_async_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._async_session is None or self._async_session.closed:
            connector = aiohttp.TCPConnector(limit=config.MAX_CONCURRENT_REQUESTS)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._async_session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.headers,
            )
        return self._async_session
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        if endpoint.startswith("http"):
            return endpoint
        return f"{self.base_url}/{endpoint.lstrip('/')}"
    
    def get(
        self,
        endpoint: str,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Make GET request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Additional headers
            
        Returns:
            JSON response or None if failed
        """
        self.rate_limiter.wait()
        
        url = self._build_url(endpoint)
        request_headers = {**self.headers, **(headers or {})}
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers=request_headers,
                    timeout=self.timeout,
                )
                
                if response.status_code == 200:
                    try:
                        return response.json()
                    except ValueError:
                        return {"text": response.text}
                
                elif response.status_code == 429:  # Rate limited
                    wait_time = int(response.headers.get("Retry-After", self.retry_delay * 2))
                    time.sleep(wait_time)
                    continue
                
                elif response.status_code >= 500:  # Server error
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                
                else:
                    return None
                    
            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return None
                
            except requests.exceptions.RequestException as e:
                console.print(f"[red]Request error: {e}[/red]")
                return None
        
        return None
    
    def post(
        self,
        endpoint: str,
        data: Dict[str, Any] = None,
        json_data: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Make POST request.
        
        Args:
            endpoint: API endpoint
            data: Form data
            json_data: JSON data
            headers: Additional headers
            
        Returns:
            JSON response or None if failed
        """
        self.rate_limiter.wait()
        
        url = self._build_url(endpoint)
        request_headers = {**self.headers, **(headers or {})}
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    url,
                    data=data,
                    json=json_data,
                    headers=request_headers,
                    timeout=self.timeout,
                )
                
                if response.status_code in [200, 201]:
                    try:
                        return response.json()
                    except ValueError:
                        return {"text": response.text}
                
                elif response.status_code == 429:
                    wait_time = int(response.headers.get("Retry-After", self.retry_delay * 2))
                    time.sleep(wait_time)
                    continue
                
                else:
                    return None
                    
            except requests.exceptions.RequestException as e:
                console.print(f"[red]Request error: {e}[/red]")
                return None
        
        return None
    
    async def async_get(
        self,
        endpoint: str,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Make async GET request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Additional headers
            
        Returns:
            JSON response or None if failed
        """
        await self.rate_limiter.async_wait()
        
        url = self._build_url(endpoint)
        request_headers = {**self.headers, **(headers or {})}
        
        session = await self.get_async_session()
        
        try:
            async with session.get(url, params=params, headers=request_headers) as response:
                if response.status == 200:
                    try:
                        return await response.json()
                    except:
                        text = await response.text()
                        return {"text": text}
                return None
                
        except asyncio.TimeoutError:
            return None
        except aiohttp.ClientError as e:
            return None
    
    async def async_get_many(
        self,
        endpoints: List[str],
        params_list: List[Dict[str, Any]] = None,
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Make multiple async GET requests.
        
        Args:
            endpoints: List of endpoints
            params_list: List of params for each endpoint
            
        Returns:
            List of responses
        """
        if params_list is None:
            params_list = [None] * len(endpoints)
        
        tasks = [
            self.async_get(endpoint, params)
            for endpoint, params in zip(endpoints, params_list)
        ]
        
        return await asyncio.gather(*tasks)
    
    async def close(self) -> None:
        """Close async session."""
        if self._async_session and not self._async_session.closed:
            await self._async_session.close()
    
    def __del__(self):
        """Cleanup on deletion."""
        if hasattr(self, '_session') and self._session:
            try:
                self._session.close()
            except:
                pass


class NumverifyClient(APIClient):
    """Client untuk Numverify API."""
    
    def __init__(self):
        super().__init__(
            base_url="http://apilayer.net/api",
            api_key=config.API_KEYS.get("numverify"),
            rate_limit=config.RATE_LIMITS.get("numverify", 1),
        )
    
    def validate(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Validate phone number."""
        params = {
            "access_key": self.api_key,
            "number": phone_number,
            "country_code": "",
            "format": 1,
        }
        return self.get("validate", params=params)


class IPInfoClient(APIClient):
    """Client untuk IPInfo API."""
    
    def __init__(self):
        super().__init__(
            base_url="https://ipinfo.io",
            api_key=config.API_KEYS.get("ipinfo"),
            rate_limit=config.RATE_LIMITS.get("ipinfo", 10),
        )
    
    def lookup(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Lookup IP address information."""
        endpoint = f"{ip_address}/json"
        params = {"token": self.api_key} if self.api_key else None
        return self.get(endpoint, params=params)


class XposedOrNotClient(APIClient):
    """Client untuk XposedOrNot API (gratis, tanpa key)."""
    
    def __init__(self):
        super().__init__(
            base_url="https://api.xposedornot.com/v1",
            rate_limit=config.RATE_LIMITS.get("xposedornot", 1),
        )
    
    def check_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Check email for breaches."""
        return self.get(f"check-email/{email}")
    
    def get_breach_analytics(self, email: str) -> Optional[Dict[str, Any]]:
        """Get breach analytics for email."""
        return self.get(f"breach-analytics?email={email}")


# Factory function
def get_api_client(service: str) -> APIClient:
    """
    Get API client for specific service.
    
    Args:
        service: Service name (numverify, ipinfo, xposedornot)
        
    Returns:
        Configured API client
    """
    clients = {
        "numverify": NumverifyClient,
        "ipinfo": IPInfoClient,
        "xposedornot": XposedOrNotClient,
    }
    
    client_class = clients.get(service)
    if client_class:
        return client_class()
    
    return APIClient()
