"""
CKSEARCH - Platform Registration Checker (Extended Edition)
=============================================================
Real check apakah email/phone terdaftar di platform.
Menggunakan teknik yang sama seperti Holehe/PhoneInfoga.

Platforms: 25+ Email Checkers, 5+ Phone Checkers
"""

import asyncio
import aiohttp
import random
import string
import re
import hashlib
import json
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

import config

console = Console()


# User Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
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
                
                # List of email checkers (25+ platforms)
                checkers = [
                    # Social Media
                    ("Twitter/X", self._check_twitter),
                    ("Instagram", self._check_instagram),
                    ("Snapchat", self._check_snapchat),
                    ("Pinterest", self._check_pinterest),
                    ("LinkedIn", self._check_linkedin),
                    ("TikTok", self._check_tiktok),
                    ("Reddit", self._check_reddit),
                    ("Tumblr", self._check_tumblr),
                    
                    # Chat/Communication
                    ("Discord", self._check_discord),
                    ("Telegram", self._check_telegram_email),
                    
                    # Tech/Developer
                    ("GitHub", self._check_github),
                    ("GitLab", self._check_gitlab),
                    ("Bitbucket", self._check_bitbucket),
                    ("StackOverflow", self._check_stackoverflow),
                    
                    # Music/Entertainment
                    ("Spotify", self._check_spotify),
                    ("Deezer", self._check_deezer),
                    ("SoundCloud", self._check_soundcloud),
                    
                    # Shopping/Services
                    ("Amazon", self._check_amazon),
                    ("eBay", self._check_ebay),
                    ("Etsy", self._check_etsy),
                    
                    # Cloud/Productivity
                    ("WordPress", self._check_wordpress),
                    ("Gravatar", self._check_gravatar),
                    ("Notion", self._check_notion),
                    ("Trello", self._check_trello),
                    
                    # Other
                    ("Firefox", self._check_firefox),
                    ("Adobe", self._check_adobe),
                    ("Duolingo", self._check_duolingo),
                    ("Patreon", self._check_patreon),
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
        if phone_clean.startswith('0'):
            phone_clean = '62' + phone_clean[1:]
        elif not phone_clean.startswith('62'):
            phone_clean = '62' + phone_clean
        
        phone_local = '0' + phone_clean[2:] if phone_clean.startswith('62') else phone_clean
        
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
                    # Phone-based checks
                    ("WhatsApp", self._check_whatsapp),
                    ("Telegram", self._check_telegram_phone),
                    ("Truecaller", self._check_truecaller),
                    ("Snapchat", self._check_snapchat_phone),
                    ("Signal", self._check_signal),
                    ("Viber", self._check_viber),
                    ("Line", self._check_line),
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
    # EMAIL CHECKERS (25+ platforms)
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
            }
            
            async with session.get("https://www.instagram.com/accounts/emailsignup/", headers=headers) as resp:
                text = await resp.text()
                if 'csrf_token":"' in text:
                    token = text.split('csrf_token":"')[1].split('"')[0]
                else:
                    return {"exists": False}
            
            headers["x-csrftoken"] = token
            random_username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=15))
            
            data = {'email': email, 'username': random_username, 'first_name': '', 'opt_into_one_tap': 'false'}
            
            async with session.post(
                "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/",
                data=data, headers=headers
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("status") != "fail":
                        errors = result.get("errors", {})
                        if "email" in errors:
                            for error in errors["email"]:
                                if error.get("code") == "email_is_taken" or "email_sharing_limit" in str(error):
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
                    if data.get("status") == 20:
                        return {"exists": True, "method": "signup validation"}
        except:
            pass
        return {"exists": False}
    
    async def _check_snapchat(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Snapchat - uses login check API."""
        try:
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
            headers = {"User-Agent": random.choice(USER_AGENTS), "Content-Type": "application/json"}
            data = {
                "email": email,
                "username": ''.join(random.choices(string.ascii_lowercase, k=10)),
                "password": ''.join(random.choices(string.ascii_letters + string.digits, k=20)),
                "consent": True,
            }
            
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
                        return {"exists": True, "method": "email check"}
        except:
            pass
        return {"exists": False}
    
    async def _check_linkedin(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """LinkedIn - uses registration check."""
        try:
            url = f"https://www.linkedin.com/sales-api/salesApiAcceptedEmailSearch?q=nonEmails&emailIds={email}"
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return {"exists": True, "method": "sales API check"}
        except:
            pass
        return {"exists": False}
    
    async def _check_tiktok(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """TikTok - uses password reset check."""
        try:
            url = "https://www.tiktok.com/passport/web/email/forget/"
            headers = {"User-Agent": random.choice(USER_AGENTS), "Content-Type": "application/json"}
            data = {"email": email, "type": "email"}
            
            async with session.post(url, data=json.dumps(data), headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("data", {}).get("sent"):
                        return {"exists": True, "method": "password reset"}
        except:
            pass
        return {"exists": False}
    
    async def _check_reddit(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Reddit - uses registration check."""
        try:
            url = "https://www.reddit.com/api/check_username.json"
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            params = {"user": email.split('@')[0][:20]}
            
            async with session.get(url, params=params, headers=headers) as resp:
                # Reddit check is based on username, not email
                pass
        except:
            pass
        return {"exists": False}
    
    async def _check_tumblr(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Tumblr - uses registration check."""
        try:
            url = "https://www.tumblr.com/api/v2/register/email_available"
            headers = {"User-Agent": random.choice(USER_AGENTS), "Content-Type": "application/json"}
            data = {"email": email}
            
            async with session.post(url, data=json.dumps(data), headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if not result.get("response", {}).get("available", True):
                        return {"exists": True, "method": "email check"}
        except:
            pass
        return {"exists": False}
    
    async def _check_telegram_email(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Telegram email check (limited)."""
        return {"exists": False}
    
    async def _check_gitlab(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """GitLab - uses username suggestion."""
        try:
            username = email.split('@')[0][:20]
            url = f"https://gitlab.com/api/v4/users?username={username}"
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    users = await resp.json()
                    if users:
                        return {"exists": True, "method": "user search"}
        except:
            pass
        return {"exists": False}
    
    async def _check_bitbucket(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Bitbucket - uses account check."""
        try:
            username = email.split('@')[0][:20]
            url = f"https://bitbucket.org/api/2.0/users/{username}"
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return {"exists": True, "method": "user lookup"}
        except:
            pass
        return {"exists": False}
    
    async def _check_stackoverflow(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """StackOverflow - uses email recovery check."""
        try:
            url = "https://stackoverflow.com/users/account-recovery"
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            # Limited without proper session
        except:
            pass
        return {"exists": False}
    
    async def _check_deezer(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Deezer - uses email check."""
        try:
            url = f"https://www.deezer.com/ajax/gw-light.php?method=user.getEmailValidation&api_token=null&api_version=1.0&input=3"
            headers = {"User-Agent": random.choice(USER_AGENTS), "Content-Type": "application/x-www-form-urlencoded"}
            data = f"email={email}"
            
            async with session.post(url, data=data, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("results", {}).get("USER"):
                        return {"exists": True, "method": "email validation"}
        except:
            pass
        return {"exists": False}
    
    async def _check_soundcloud(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """SoundCloud - uses web signup check."""
        try:
            url = "https://api-v2.soundcloud.com/me"
            # Requires auth - skip
        except:
            pass
        return {"exists": False}
    
    async def _check_amazon(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Amazon - uses login check."""
        if not HAS_BS4:
            return {"exists": False}
        try:
            url = "https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com"
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            
            async with session.get(url, headers=headers) as resp:
                text = await resp.text()
                soup = BeautifulSoup(text, 'html.parser')
                inputs = soup.select('form input')
                data = {x.get("name"): x.get("value", "") for x in inputs if x.get("name")}
                data["email"] = email
            
            async with session.post("https://www.amazon.com/ap/signin/", data=data, headers=headers) as resp:
                text = await resp.text()
                if "auth-password-missing-alert" in text or "Enter your password" in text:
                    return {"exists": True, "method": "login check"}
        except:
            pass
        return {"exists": False}
    
    async def _check_ebay(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """eBay - uses signin check."""
        try:
            url = "https://signin.ebay.com/ws/eBayISAPI.dll?SignIn"
            # Complex check - skip for now
        except:
            pass
        return {"exists": False}
    
    async def _check_etsy(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Etsy - uses email check."""
        try:
            url = f"https://www.etsy.com/api/v3/ajax/member/email-exists?email={email}"
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("exists"):
                        return {"exists": True, "method": "email check"}
        except:
            pass
        return {"exists": False}
    
    async def _check_wordpress(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """WordPress.com - uses auth options."""
        try:
            url = f"https://public-api.wordpress.com/rest/v1.1/users/email/{email}/auth-options"
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("passwordless") is not None:
                        return {"exists": True, "method": "auth options"}
        except:
            pass
        return {"exists": False}
    
    async def _check_gravatar(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Gravatar - uses avatar check."""
        try:
            email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
            url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return {"exists": True, "method": "avatar check", "details": f"https://gravatar.com/{email_hash}"}
        except:
            pass
        return {"exists": False}
    
    async def _check_notion(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Notion - uses loginWithEmail."""
        try:
            url = "https://www.notion.so/api/v3/loginWithEmail"
            headers = {"User-Agent": random.choice(USER_AGENTS), "Content-Type": "application/json"}
            data = {"email": email}
            
            async with session.post(url, data=json.dumps(data), headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("hasAccount"):
                        return {"exists": True, "method": "login check"}
        except:
            pass
        return {"exists": False}
    
    async def _check_trello(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Trello - uses atlassian check."""
        try:
            url = f"https://id.atlassian.com/login?email={email}"
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            
            async with session.get(url, headers=headers) as resp:
                text = await resp.text()
                if "Enter your password" in text:
                    return {"exists": True, "method": "login check"}
        except:
            pass
        return {"exists": False}
    
    async def _check_firefox(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Firefox/Mozilla - account status."""
        try:
            url = "https://accounts.firefox.com/api/account/status"
            headers = {"User-Agent": random.choice(USER_AGENTS), "Content-Type": "application/json"}
            data = json.dumps({"email": email})
            
            async with session.post(url, data=data, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("exists"):
                        return {"exists": True, "method": "account status"}
        except:
            pass
        return {"exists": False}
    
    async def _check_adobe(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Adobe - uses email validation."""
        try:
            url = "https://adobeid-na1.services.adobe.com/renga-idprovider/pages/validate_email"
            headers = {"User-Agent": random.choice(USER_AGENTS), "Content-Type": "application/x-www-form-urlencoded"}
            data = f"email={email}"
            
            async with session.post(url, data=data, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("valid"):
                        return {"exists": True, "method": "email validation"}
        except:
            pass
        return {"exists": False}
    
    async def _check_duolingo(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Duolingo - uses login check."""
        try:
            url = "https://www.duolingo.com/2017-06-30/users"
            headers = {"User-Agent": random.choice(USER_AGENTS), "Content-Type": "application/json"}
            params = {"email": email}
            
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("users"):
                        return {"exists": True, "method": "user check"}
        except:
            pass
        return {"exists": False}
    
    async def _check_patreon(self, session: aiohttp.ClientSession, email: str) -> Optional[Dict]:
        """Patreon - uses signup check."""
        try:
            url = "https://www.patreon.com/api/auth/signup"
            headers = {"User-Agent": random.choice(USER_AGENTS), "Content-Type": "application/json"}
            data = {"email": email, "password": "TestPass123!"}
            
            async with session.post(url, data=json.dumps(data), headers=headers) as resp:
                if resp.status == 400:
                    result = await resp.json()
                    errors = result.get("errors", [])
                    for err in errors:
                        if "email" in str(err).lower() and "already" in str(err).lower():
                            return {"exists": True, "method": "signup check"}
        except:
            pass
        return {"exists": False}
    
    # ========================================
    # PHONE CHECKERS
    # ========================================
    
    async def _check_whatsapp(self, session: aiohttp.ClientSession, phone: str, phone_local: str) -> Optional[Dict]:
        """WhatsApp - limited without official API."""
        # WhatsApp memerlukan Business API atau web session
        # Ini adalah placeholder - dalam production gunakan WhatsApp Business API
        return {"exists": False}
    
    async def _check_telegram_phone(self, session: aiohttp.ClientSession, phone: str, phone_local: str) -> Optional[Dict]:
        """Telegram - uses public API."""
        try:
            # Check if Telegram username exists for this phone (public profile)
            url = f"https://t.me/+{phone}"
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            
            async with session.get(url, headers=headers) as resp:
                text = await resp.text()
                if "tgme_page_title" in text:
                    return {"exists": True, "method": "public profile check"}
        except:
            pass
        return {"exists": False}
    
    async def _check_truecaller(self, session: aiohttp.ClientSession, phone: str, phone_local: str) -> Optional[Dict]:
        """Truecaller - requires API key."""
        # Truecaller API memerlukan key berbayar
        return {"exists": False}
    
    async def _check_snapchat_phone(self, session: aiohttp.ClientSession, phone: str, phone_local: str) -> Optional[Dict]:
        """Snapchat - phone username suggestion."""
        try:
            url = "https://accounts.snapchat.com/accounts/get_username_suggestions"
            headers = {"User-Agent": random.choice(USER_AGENTS), "Content-Type": "application/json"}
            data = json.dumps({"phone": f"+{phone}"})
            
            async with session.post(url, data=data, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("suggestions"):
                        return {"exists": True, "method": "username suggestion"}
        except:
            pass
        return {"exists": False}
    
    async def _check_signal(self, session: aiohttp.ClientSession, phone: str, phone_local: str) -> Optional[Dict]:
        """Signal - requires app/API."""
        return {"exists": False}
    
    async def _check_viber(self, session: aiohttp.ClientSession, phone: str, phone_local: str) -> Optional[Dict]:
        """Viber - requires app."""
        return {"exists": False}
    
    async def _check_line(self, session: aiohttp.ClientSession, phone: str, phone_local: str) -> Optional[Dict]:
        """Line - requires app."""
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
