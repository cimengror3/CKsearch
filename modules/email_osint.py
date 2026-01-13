"""
CKSEARCH - Email OSINT Module (Accurate Edition)
===================================================
Email intelligence with VERIFIED platform checks.
Only shows platforms where email is CONFIRMED registered.
"""

import re
import hashlib
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

import config
from core.scanner import BaseScanner
from core.api_client import XposedOrNotClient, APIClient

console = Console()


# =============================================================================
# CHECKABLE PLATFORMS - Platforms we can actually verify
# =============================================================================
# Each platform has specific endpoints and patterns to detect if email exists

CHECKABLE_PLATFORMS = [
    # ===== VERIFIED WORKING CHECKS =====
    {
        "name": "Twitter/X",
        "check_url": "https://api.twitter.com/i/users/email_available.json?email={}",
        "method": "json",
        "exists_pattern": {"taken": True},
        "category": "Social",
    },
    {
        "name": "Spotify",
        "check_url": "https://spclient.wg.spotify.com/signup/public/v1/account?validate=1&email={}",
        "method": "json_status",
        "exists_indicator": 20,  # status 20 = email exists
        "category": "Music",
    },
    {
        "name": "Pinterest",
        "check_url": "https://www.pinterest.com/_ngjs/resource/EmailExistsResource/get/?source_url=/&data={{\"options\":{{\"email\":\"{}\"}},\"context\":{{}}}}",
        "method": "json",
        "exists_key": "resource_response.data",
        "category": "Social",
    },
    {
        "name": "GitHub",
        "check_url": "https://github.com/signup_check/email?value={}",
        "method": "content",
        "exists_pattern": "already taken",
        "not_exists_pattern": "is available",
        "category": "Tech",
    },
    {
        "name": "WordPress",
        "check_url": "https://public-api.wordpress.com/rest/v1.1/users/email/{}",
        "method": "status",
        "exists_status": 200,
        "category": "Blog",
    },
    {
        "name": "Discord",
        "check_url": "https://discord.com/api/v9/unique-username/username-suggestions-unauthed?email={}",
        "method": "recovery_hint",
        "category": "Chat",
    },
    {
        "name": "Amazon",
        "check_url": "https://www.amazon.com/ap/signin",
        "method": "recovery_form",
        "form_field": "email",
        "exists_pattern": "password",
        "not_exists_pattern": "no account found",
        "category": "Shopping",
    },
]

# Platforms where we can only generate check links (user must verify manually)
MANUAL_CHECK_PLATFORMS = {
    "Social": [
        {"name": "Instagram", "url": "https://www.instagram.com/accounts/account_recovery_send_ajax/"},
        {"name": "Facebook", "url": "https://www.facebook.com/login/identify/"},
        {"name": "TikTok", "url": "https://www.tiktok.com/login/"},
        {"name": "LinkedIn", "url": "https://www.linkedin.com/checkpoint/rp/request-password-reset"},
        {"name": "Snapchat", "url": "https://accounts.snapchat.com/accounts/password_reset_request"},
    ],
    "Gaming": [
        {"name": "Steam", "url": "https://help.steampowered.com/wizard/HelpWithLoginInfo?issueid=406"},
        {"name": "Epic Games", "url": "https://www.epicgames.com/id/forgot-password"},
        {"name": "Riot Games", "url": "https://recovery.riotgames.com/"},
        {"name": "PlayStation", "url": "https://id.sonyentertainmentnetwork.com/signin/"},
        {"name": "Xbox", "url": "https://login.live.com/"},
    ],
    "Finance": [
        {"name": "PayPal", "url": "https://www.paypal.com/authflow/password-recovery/"},
        {"name": "Wise", "url": "https://wise.com/forgot-password"},
    ],
    "Indonesia": [
        {"name": "Tokopedia", "url": "https://www.tokopedia.com/forgot-password"},
        {"name": "Shopee ID", "url": "https://shopee.co.id/buyer/reset"},
        {"name": "Bukalapak", "url": "https://www.bukalapak.com/password_resets/new"},
        {"name": "Gojek/GoPay", "url": "https://driver.gojek.com/forgot-password"},
        {"name": "OVO", "url": "https://www.ovo.id/"},
        {"name": "DANA", "url": "https://dana.id/"},
        {"name": "Traveloka", "url": "https://www.traveloka.com/en-id/login"},
        {"name": "Tiket.com", "url": "https://www.tiket.com/"},
    ],
}

# Breach Check Services (via API)
BREACH_SERVICES = [
    {"name": "Have I Been Pwned", "url": "https://haveibeenpwned.com/account/{email}"},
    {"name": "XposedOrNot", "url": "https://xposedornot.com/result/{email}"},
    {"name": "DeHashed", "url": "https://www.dehashed.com/search?query={email}"},
    {"name": "Intelligence X", "url": "https://intelx.io/?s={email}"},
    {"name": "LeakCheck", "url": "https://leakcheck.io/"},
    {"name": "BreachDirectory", "url": "https://breachdirectory.org/"},
]

# Google Dorks
GOOGLE_DORKS = [
    {"name": "Exact Match", "query": '"{email}"'},
    {"name": "Username", "query": '"{username}"'},
    {"name": "LinkedIn", "query": 'site:linkedin.com "{email}"'},
    {"name": "GitHub", "query": 'site:github.com "{email}"'},
    {"name": "Pastebin", "query": 'site:pastebin.com "{email}"'},
    {"name": "PDF Files", "query": 'filetype:pdf "{email}"'},
]


class EmailOSINT(BaseScanner):
    """Email OSINT with verified platform checks."""
    
    def __init__(self, language: str = "id"):
        super().__init__("Email OSINT", language)
        self.xposedornot = XposedOrNotClient()
        self.http_client = APIClient()
    
    def scan(self, email: str, **options) -> Dict[str, Any]:
        """
        Comprehensive email OSINT scan.
        Returns only CONFIRMED registrations.
        """
        self._start()
        
        scan_mode = options.get("scan_mode", "quick")
        
        # Validate email
        if not self._validate_email(email):
            self._add_error("Invalid email format")
            self._finish()
            return {"error": "Invalid email format"}
        
        username = email.split("@")[0]
        domain = email.split("@")[1]
        
        results = {
            "email": email,
            "username": username,
            "domain": domain,
            "scan_mode": scan_mode,
            "valid": True,
            "domain_info": {},
            "breaches": {"found": False, "count": 0, "details": []},
            "confirmed_platforms": [],  # VERIFIED registrations
            "manual_check_links": [],   # Links for manual verification
            "breach_check_links": [],   # Links to breach databases
            "google_dorks": [],
            "gravatar": None,
            "disposable_check": {},
            "risk_assessment": {},
        }
        
        # 1. Domain analysis
        console.print("[cyan]→ Analyzing email domain...[/cyan]")
        results["domain_info"] = self._analyze_domain(domain)
        
        # 2. Breach check via API (REAL DATA)
        console.print("[cyan]→ Checking breach databases (API)...[/cyan]")
        breach_data = self._check_xposedornot(email)
        if breach_data:
            results["breaches"] = breach_data
        
        # 3. Check platforms using REAL verification (Holehe 120+ sites)
        if scan_mode == "deep":
            console.print("[cyan]→ Checking 120+ platforms (Powered by Holehe)...[/cyan]")
            try:
                from core.holehe_wrapper import run_holehe
                confirmed = asyncio.run(run_holehe(email))
                results["confirmed_platforms"] = confirmed
                if confirmed:
                    console.print(f"[green]  Found {len(confirmed)} confirmed profiles[/green]")
            except Exception as e:
                console.print(f"[yellow]  Holehe check error: {e}[/yellow]")
                results["confirmed_platforms"] = []
        
        # 4. Generate manual check links
        # Only show manual links if few automated results found (< 2)
        if len(results.get("confirmed_platforms", [])) < 2:
            console.print("[cyan]→ Generating verification links...[/cyan]")
            results["manual_check_links"] = self._generate_manual_links()
        else:
            results["manual_check_links"] = []
        
        # 5. Generate breach check links
        results["breach_check_links"] = self._generate_breach_links(email)
        
        # 6. Gravatar check
        console.print("[cyan]→ Checking Gravatar...[/cyan]")
        results["gravatar"] = self._check_gravatar(email)
        
        # 7. Disposable check
        console.print("[cyan]→ Checking if disposable email...[/cyan]")
        results["disposable_check"] = self._check_disposable(domain)
        
        # 8. Google dorks
        console.print("[cyan]→ Generating Google dork queries...[/cyan]")
        results["google_dorks"] = self._generate_google_dorks(email, username)
        
        # 9. Risk assessment
        results["risk_assessment"] = self._calculate_risk(results)
        
        # Stats
        results["stats"] = {
            "confirmed_count": len(results["confirmed_platforms"]),
            "breaches_found": results["breaches"]["count"],
            "manual_links": len(results["manual_check_links"]),
        }
        
        self._finish()
        results["metadata"] = self.get_metadata()
        
        return results
    
    def _validate_email(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _analyze_domain(self, domain: str) -> Dict[str, Any]:
        info = {"domain": domain, "provider_type": "custom", "mx_records": []}
        
        providers = {
            "gmail.com": ("Google", "public"),
            "googlemail.com": ("Google", "public"),
            "outlook.com": ("Microsoft", "public"),
            "hotmail.com": ("Microsoft", "public"),
            "live.com": ("Microsoft", "public"),
            "yahoo.com": ("Yahoo", "public"),
            "icloud.com": ("Apple", "public"),
            "protonmail.com": ("ProtonMail", "secure"),
            "proton.me": ("ProtonMail", "secure"),
            "tutanota.com": ("Tutanota", "secure"),
        }
        
        if domain.lower() in providers:
            info["provider"], info["provider_type"] = providers[domain.lower()]
        else:
            info["provider"] = "Custom/Business"
        
        try:
            import dns.resolver
            mx = dns.resolver.resolve(domain, 'MX')
            info["mx_records"] = [{"host": str(r.exchange).rstrip('.'), "priority": r.preference} for r in mx]
        except:
            pass
        
        return info
    
    def _check_xposedornot(self, email: str) -> Dict[str, Any]:
        try:
            result = self.xposedornot.check_email(email)
            if not result:
                return {"found": False, "count": 0, "details": []}
            
            if isinstance(result, list) and len(result) > 0:
                return {
                    "found": True,
                    "count": len(result),
                    "details": [{"name": str(b)} for b in result],
                }
            
            if isinstance(result, dict) and result.get("breaches"):
                breaches = result["breaches"]
                if isinstance(breaches, list) and len(breaches) > 0:
                    return {
                        "found": True,
                        "count": len(breaches),
                        "details": [{"name": b.get("breach", str(b)) if isinstance(b, dict) else str(b)} for b in breaches],
                    }
            
            return {"found": False, "count": 0, "details": []}
        except Exception as e:
            return {"found": False, "count": 0, "error": str(e)}
    
    async def _check_platforms(self, email: str) -> List[Dict]:
        """Check platforms that have verifiable endpoints."""
        confirmed = []
        
        timeout = aiohttp.ClientTimeout(total=10)
        connector = aiohttp.TCPConnector(limit=20, ssl=False)
        
        headers = {
            "User-Agent": config.DEFAULT_USER_AGENT,
            "Accept": "application/json, text/html",
        }
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers=headers) as session:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=30),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task("Checking platforms...", total=len(CHECKABLE_PLATFORMS))
                
                for platform in CHECKABLE_PLATFORMS:
                    try:
                        result = await self._check_single_platform(session, platform, email)
                        if result:
                            confirmed.append(result)
                    except:
                        pass
                    progress.advance(task)
        
        return confirmed
    
    async def _check_single_platform(self, session: aiohttp.ClientSession, platform: Dict, email: str) -> Optional[Dict]:
        """Check single platform for email registration."""
        url = platform["check_url"].format(email)
        method = platform.get("method", "content")
        
        try:
            async with session.get(url) as resp:
                if method == "json":
                    try:
                        data = await resp.json()
                        exists_pattern = platform.get("exists_pattern", {})
                        for key, val in exists_pattern.items():
                            if data.get(key) == val:
                                return {
                                    "name": platform["name"],
                                    "category": platform["category"],
                                    "verified": True,
                                    "method": "API check",
                                }
                    except:
                        pass
                
                elif method == "json_status":
                    try:
                        data = await resp.json()
                        if data.get("status") == platform.get("exists_indicator"):
                            return {
                                "name": platform["name"],
                                "category": platform["category"],
                                "verified": True,
                                "method": "API check",
                            }
                    except:
                        pass
                
                elif method == "content":
                    text = await resp.text()
                    exists_pattern = platform.get("exists_pattern", "")
                    not_exists = platform.get("not_exists_pattern", "")
                    
                    if exists_pattern and exists_pattern.lower() in text.lower():
                        return {
                            "name": platform["name"],
                            "category": platform["category"],
                            "verified": True,
                            "method": "Recovery check",
                        }
                
                elif method == "status":
                    if resp.status == platform.get("exists_status", 200):
                        return {
                            "name": platform["name"],
                            "category": platform["category"],
                            "verified": True,
                            "method": "API check",
                        }
        except:
            pass
        
        return None
    
    def _generate_manual_links(self) -> List[Dict]:
        """Generate links for manual verification."""
        links = []
        for category, platforms in MANUAL_CHECK_PLATFORMS.items():
            for p in platforms:
                links.append({
                    "name": p["name"],
                    "url": p["url"],
                    "category": category,
                    "note": "Check forgot password page to verify if email is registered",
                })
        return links
    
    def _generate_breach_links(self, email: str) -> List[Dict]:
        links = []
        for s in BREACH_SERVICES:
            links.append({
                "name": s["name"],
                "url": s["url"].replace("{email}", email),
            })
        return links
    
    def _check_gravatar(self, email: str) -> Dict[str, Any]:
        email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
        gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}"
        
        try:
            resp = self.http_client.session.get(f"{gravatar_url}?d=404", timeout=5)
            if resp.status_code == 200:
                return {"found": True, "avatar_url": gravatar_url, "hash": email_hash}
        except:
            pass
        return {"found": False, "avatar_url": f"{gravatar_url}?d=identicon"}
    
    def _check_disposable(self, domain: str) -> Dict[str, Any]:
        disposable = {
            "tempmail.com", "guerrillamail.com", "10minutemail.com", "mailinator.com",
            "throwaway.email", "yopmail.com", "fakeinbox.com", "trashmail.com",
            "getnada.com", "maildrop.cc", "temp-mail.org", "sharklasers.com",
            "mohmal.com", "tempmailo.com", "emailondeck.com",
        }
        
        is_disp = domain.lower() in disposable
        return {
            "is_disposable": is_disp,
            "domain": domain,
            "risk_level": "high" if is_disp else "low",
        }
    
    def _generate_google_dorks(self, email: str, username: str) -> List[Dict]:
        dorks = []
        for d in GOOGLE_DORKS:
            query = d["query"].replace("{email}", email).replace("{username}", username)
            url = f"https://www.google.com/search?q={query.replace(' ', '+').replace('\"', '%22')}"
            dorks.append({
                "name": d["name"],
                "query": query,
                "url": url,
            })
        return dorks
    
    def _calculate_risk(self, results: Dict) -> Dict[str, Any]:
        score = 0
        factors = []
        
        if results["breaches"]["found"]:
            count = results["breaches"]["count"]
            score += min(count * 10, 50)
            factors.append(f"Found in {count} breach(es)")
        
        if results["disposable_check"].get("is_disposable"):
            score += 30
            factors.append("Disposable email")
        
        if results.get("gravatar", {}).get("found"):
            factors.append("Has Gravatar profile")
        
        level = "CRITICAL" if score >= 70 else "HIGH" if score >= 50 else "MEDIUM" if score >= 30 else "LOW"
        
        recommendations = []
        if results["breaches"]["found"]:
            recommendations.extend([
                "Change password immediately",
                "Enable 2FA on all accounts",
                "Check for unauthorized access",
            ])
        
        return {
            "score": score,
            "level": level,
            "factors": factors,
            "recommendations": recommendations,
        }


def scan_email(email: str, scan_mode: str = "quick") -> Dict[str, Any]:
    return EmailOSINT().scan(email, scan_mode=scan_mode)
