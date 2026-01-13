"""
CKSEARCH - Platform Registration Checker
==========================================
Real check apakah email/phone terdaftar di platform.
Menggunakan teknik yang sama seperti Holehe/PhoneInfoga.
"""

import asyncio
import aiohttp
import random
import string
import re
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

import config

console = Console()


# User Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


class PlatformChecker:
    """Check if email/phone is registered on various platforms."""
    
    def __init__(self):
        self.results = []
    
    async def check_all_email(self, email: str) -> List[Dict]:
        """Check email on all supported platforms."""
        self.results = []
        
        timeout = aiohttp.ClientTimeout(total=15)
        connector = aiohttp.TCPConnector(limit=10, ssl=False)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=30),
                TaskProgressColumn(),
                TextColumn("[green]Found: {task.fields[found]}[/green]"),
                console=console
            ) as progress:
                
                # List of checkers
                checkers = [
                    ("Twitter/X", self._check_twitter),
                    ("Instagram", self._check_instagram),
                    ("Spotify", self._check_spotify),
                    ("Snapchat", self._check_snapchat),
                    ("Discord", self._check_discord),
                    ("GitHub", self._check_github),
                    ("Pinterest", self._check_pinterest),
                    ("Adobe", self._check_adobe),
                    ("WordPress", self._check_wordpress),
                    ("Gravatar", self._check_gravatar),
                    ("Firefox", self._check_firefox),
                ]
                
                found = 0
                task = progress.add_task("Checking platforms...", total=len(checkers), found=0)
                
                for name, checker in checkers:
                    try:
                        result = await checker(session, email)
                        if result and result.get("exists"):
                            self.results.append({
                                "platform": name,
                                "exists": True,
                                "method": result.get("method", "unknown"),
                                "details": result.get("details"),
                            })
                            found += 1
                    except Exception as e:
                        pass  # Silently skip errors
                    
                    progress.update(task, advance=1, found=found)
        
        return self.results
    
    async def check_all_phone(self, phone: str) -> List[Dict]:
        """Check phone number on supported platforms."""
        self.results = []
        
        # Format nomor ke berbagai format
        phone_clean = re.sub(r'[^\d]', '', phone)
        if phone_clean.startswith('62'):
            phone_local = '0' + phone_clean[2:]
        else:
            phone_local = phone_clean
        
        timeout = aiohttp.ClientTimeout(total=15)
        connector = aiohttp.TCPConnector(limit=10, ssl=False)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=30),
                TaskProgressColumn(),
                TextColumn("[green]Found: {task.fields[found]}[/green]"),
                console=console
            ) as progress:
                
                checkers = [
                    ("WhatsApp", self._check_whatsapp),
                    ("Telegram", self._check_telegram),
                    ("Snapchat Phone", self._check_snapchat_phone),
                ]
                
                found = 0
                task = progress.add_task("Checking platforms...", total=len(checkers), found=0)
                
                for name, checker in checkers:
                    try:
                        result = await checker(session, phone_clean, phone_local)
                        if result and result.get("exists"):
                            self.results.append({
                                "platform": name,
                                "exists": True,
                                "method": result.get("method", "unknown"),
                                "details": result.get("details"),
                            })
                            found += 1
                    except:
                        pass
                    
                    progress.update(task, advance=1, found=found)
        
        return self.results
    
    # ========================================
    # EMAIL CHECKERS
    # ========================================
    
    async def _check_twitter(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Twitter - uses email_available API."""
        try:
            url = "https://api.twitter.com/i/users/email_available.json"
            params = {"email": email}
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("taken"):
                        return {"exists": True, "method": "email_available API"}
        except:
            pass
        return {"exists": False}
    
    async def _check_instagram(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Instagram - uses registration attempt API."""
        try:
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Origin': 'https://www.instagram.com',
                'DNT': '1',
                'Connection': 'keep-alive',
            }
            
            # Get CSRF token
            async with session.get("https://www.instagram.com/accounts/emailsignup/", headers=headers) as resp:
                text = await resp.text()
                if '{"config":{"csrf_token":"' in text:
                    token = text.split('{"config":{"csrf_token":"')[1].split('"')[0]
                elif 'csrf_token":"' in text:
                    token = text.split('csrf_token":"')[1].split('"')[0]
                else:
                    return {"exists": False}
            
            # Try registration
            headers["x-csrftoken"] = token
            random_username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(10, 20)))
            
            data = {
                'email': email,
                'username': random_username,
                'first_name': '',
                'opt_into_one_tap': 'false'
            }
            
            async with session.post(
                "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/",
                data=data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("status") != "fail":
                        errors = result.get("errors", {})
                        if "email" in errors:
                            for error in errors["email"]:
                                if error.get("code") == "email_is_taken":
                                    return {"exists": True, "method": "registration check"}
                                if "email_sharing_limit" in str(error):
                                    return {"exists": True, "method": "registration check"}
        except:
            pass
        return {"exists": False}
    
    async def _check_spotify(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Spotify - uses signup validation endpoint."""
        try:
            url = f"https://spclient.wg.spotify.com/signup/public/v1/account?validate=1&email={email}"
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Status 20 = email already registered
                    if data.get("status") == 20:
                        return {"exists": True, "method": "signup validation"}
        except:
            pass
        return {"exists": False}
    
    async def _check_snapchat(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Snapchat - uses login check API."""
        try:
            # Get tokens
            async with session.get("https://accounts.snapchat.com") as resp:
                text = await resp.text()
                if 'data-xsrf="' in text:
                    xsrf = text.split('data-xsrf="')[1].split('"')[0]
                    webClientId = text.split('ata-web-client-id="')[1].split('"')[0]
                else:
                    return {"exists": False}
            
            url = "https://accounts.snapchat.com/accounts/merlin/login"
            headers = {
                "Host": "accounts.snapchat.com",
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "*/*",
                "X-XSRF-TOKEN": xsrf,
                "Content-Type": "application/json",
                "Cookie": f"xsrf_token={xsrf}; web_client_id={webClientId}"
            }
            data = f'{{"email":"{email}","app":"BITMOJI_APP"}}'
            
            async with session.post(url, data=data, headers=headers) as resp:
                if resp.status != 204:
                    result = await resp.json()
                    if result.get("hasSnapchat"):
                        return {"exists": True, "method": "login check"}
        except:
            pass
        return {"exists": False}
    
    async def _check_discord(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Discord - uses auth register endpoint."""
        try:
            url = "https://discord.com/api/v9/auth/register"
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Content-Type": "application/json",
            }
            data = {
                "email": email,
                "username": ''.join(random.choices(string.ascii_lowercase, k=10)),
                "password": ''.join(random.choices(string.ascii_letters + string.digits, k=20)),
                "consent": True,
            }
            
            import json
            async with session.post(url, data=json.dumps(data), headers=headers) as resp:
                if resp.status == 400:
                    result = await resp.json()
                    errors = result.get("errors", {})
                    if "email" in errors:
                        email_errors = errors["email"].get("_errors", [])
                        for err in email_errors:
                            if "already registered" in err.get("message", "").lower():
                                return {"exists": True, "method": "registration check"}
        except:
            pass
        return {"exists": False}
    
    async def _check_github(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """GitHub - uses signup check endpoint."""
        try:
            url = f"https://github.com/signup_check/email?value={email}"
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if "already taken" in text.lower():
                        return {"exists": True, "method": "signup check"}
        except:
            pass
        return {"exists": False}
    
    async def _check_pinterest(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Pinterest - uses email exists resource."""
        try:
            import urllib.parse
            data = {"options": {"email": email}, "context": {}}
            encoded = urllib.parse.quote(str(data).replace("'", '"'))
            url = f"https://www.pinterest.com/_ngjs/resource/EmailExistsResource/get/?source_url=/&data={encoded}"
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("resource_response", {}).get("data"):
                        return {"exists": True, "method": "email exists check"}
        except:
            pass
        return {"exists": False}
    
    async def _check_adobe(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Adobe - uses forgot password check."""
        try:
            url = "https://adobeid-na1.services.adobe.com/renga-idprovider/pages/validate_email"
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Content-Type": "application/x-www-form-urlencoded",
            }
            data = f"email={email}"
            
            async with session.post(url, data=data, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("valid"):
                        return {"exists": True, "method": "email validation"}
        except:
            pass
        return {"exists": False}
    
    async def _check_wordpress(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """WordPress.com - uses user email API."""
        try:
            url = f"https://public-api.wordpress.com/rest/v1.1/users/email/{email}/auth-options"
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("passwordless"):
                        return {"exists": True, "method": "auth options check"}
        except:
            pass
        return {"exists": False}
    
    async def _check_gravatar(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Gravatar - uses avatar check with 404 default."""
        try:
            import hashlib
            email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
            url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return {"exists": True, "method": "avatar check", "details": f"https://gravatar.com/{email_hash}"}
        except:
            pass
        return {"exists": False}
    
    async def _check_firefox(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Firefox/Mozilla - uses accounts status check."""
        try:
            url = "https://accounts.firefox.com/api/account/status"
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Content-Type": "application/json",
            }
            import json
            data = json.dumps({"email": email})
            
            async with session.post(url, data=data, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("exists"):
                        return {"exists": True, "method": "account status check"}
        except:
            pass
        return {"exists": False}
    
    # ========================================
    # PHONE CHECKERS  
    # ========================================
    
    async def _check_whatsapp(self, session: aiohttp.ClientSession, phone: str, phone_local: str) -> Optional[Dict]:
        """WhatsApp - check via web interface (limited)."""
        # Note: Real WhatsApp check memerlukan session yang sudah login
        # Ini hanya placeholder - untuk implementasi nyata perlu integration lebih dalam
        return {"exists": False}
    
    async def _check_telegram(self, session: aiohttp.ClientSession, phone: str, phone_local: str) -> Optional[Dict]:
        """Telegram - check via web/API (limited)."""
        # Note: Telegram API memerlukan API credentials
        return {"exists": False}
    
    async def _check_snapchat_phone(self, session: aiohttp.ClientSession, phone: str, phone_local: str) -> Optional[Dict]:
        """Snapchat - check phone via suggest username."""
        try:
            url = "https://accounts.snapchat.com/accounts/get_username_suggestions"
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Content-Type": "application/json",
            }
            import json
            data = json.dumps({"phone": f"+{phone}"})
            
            async with session.post(url, data=data, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("suggestions"):
                        return {"exists": True, "method": "username suggestion"}
        except:
            pass
        return {"exists": False}


def check_email(email: str) -> List[Dict]:
    """Check email on all platforms."""
    checker = PlatformChecker()
    return asyncio.run(checker.check_all_email(email))


def check_phone(phone: str) -> List[Dict]:
    """Check phone on supported platforms."""
    checker = PlatformChecker()
    return asyncio.run(checker.check_all_phone(phone))


def display_results(results: List[Dict], target: str):
    """Display results in a nice table."""
    if not results:
        console.print(f"\n[yellow]⚠ No confirmed registrations found for: {target}[/yellow]")
        return
    
    table = Table(title=f"✅ Confirmed Registrations for: {target}")
    table.add_column("Platform", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Method", style="dim")
    table.add_column("Details", style="dim")
    
    for r in results:
        table.add_row(
            r["platform"],
            "✓ Registered",
            r.get("method", ""),
            r.get("details", "") or ""
        )
    
    console.print(table)
    console.print(f"\n[green]Found {len(results)} confirmed registration(s)[/green]")
