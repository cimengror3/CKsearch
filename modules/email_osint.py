"""
CKSEARCH - Email OSINT Module (Ultimate Edition)
==================================================
Comprehensive email intelligence with 100+ platform checks.
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
# EMAIL PLATFORM DATABASE - 100+ Sites
# =============================================================================

# Social Media Platforms
EMAIL_SOCIAL = [
    {"name": "Instagram", "category": "Social", "method": "recovery"},
    {"name": "Facebook", "category": "Social", "method": "recovery"},
    {"name": "Twitter/X", "category": "Social", "method": "recovery"},
    {"name": "TikTok", "category": "Social", "method": "recovery"},
    {"name": "Snapchat", "category": "Social", "method": "recovery"},
    {"name": "Pinterest", "category": "Social", "method": "recovery"},
    {"name": "LinkedIn", "category": "Professional", "method": "recovery"},
    {"name": "Reddit", "category": "Social", "method": "recovery"},
    {"name": "Tumblr", "category": "Social", "method": "recovery"},
    {"name": "Discord", "category": "Chat", "method": "recovery"},
    {"name": "Telegram", "category": "Chat", "method": "recovery"},
    {"name": "VK", "category": "Social", "method": "recovery"},
    {"name": "Quora", "category": "Social", "method": "recovery"},
]

# Streaming & Entertainment
EMAIL_STREAMING = [
    {"name": "Spotify", "category": "Music", "method": "recovery"},
    {"name": "Netflix", "category": "Streaming", "method": "recovery"},
    {"name": "Disney+", "category": "Streaming", "method": "recovery"},
    {"name": "Amazon Prime", "category": "Streaming", "method": "recovery"},
    {"name": "HBO Max", "category": "Streaming", "method": "recovery"},
    {"name": "Hulu", "category": "Streaming", "method": "recovery"},
    {"name": "Apple TV+", "category": "Streaming", "method": "recovery"},
    {"name": "YouTube", "category": "Video", "method": "recovery"},
    {"name": "Twitch", "category": "Gaming", "method": "recovery"},
    {"name": "Deezer", "category": "Music", "method": "recovery"},
    {"name": "SoundCloud", "category": "Music", "method": "recovery"},
    {"name": "Tidal", "category": "Music", "method": "recovery"},
]

# Gaming Platforms
EMAIL_GAMING = [
    {"name": "Steam", "category": "Gaming", "method": "recovery"},
    {"name": "Epic Games", "category": "Gaming", "method": "recovery"},
    {"name": "EA/Origin", "category": "Gaming", "method": "recovery"},
    {"name": "Ubisoft", "category": "Gaming", "method": "recovery"},
    {"name": "Battle.net", "category": "Gaming", "method": "recovery"},
    {"name": "Riot Games", "category": "Gaming", "method": "recovery"},
    {"name": "PlayStation", "category": "Gaming", "method": "recovery"},
    {"name": "Xbox", "category": "Gaming", "method": "recovery"},
    {"name": "Nintendo", "category": "Gaming", "method": "recovery"},
    {"name": "Roblox", "category": "Gaming", "method": "recovery"},
    {"name": "Minecraft", "category": "Gaming", "method": "recovery"},
]

# E-commerce & Shopping
EMAIL_SHOPPING = [
    {"name": "Amazon", "category": "Shopping", "method": "recovery"},
    {"name": "eBay", "category": "Shopping", "method": "recovery"},
    {"name": "AliExpress", "category": "Shopping", "method": "recovery"},
    {"name": "Shopify", "category": "Shopping", "method": "recovery"},
    {"name": "Etsy", "category": "Shopping", "method": "recovery"},
    {"name": "Walmart", "category": "Shopping", "method": "recovery"},
    {"name": "Best Buy", "category": "Shopping", "method": "recovery"},
    {"name": "Target", "category": "Shopping", "method": "recovery"},
]

# Indonesia E-commerce
EMAIL_INDONESIA = [
    {"name": "Tokopedia", "category": "Indonesia", "method": "recovery"},
    {"name": "Shopee ID", "category": "Indonesia", "method": "recovery"},
    {"name": "Bukalapak", "category": "Indonesia", "method": "recovery"},
    {"name": "Blibli", "category": "Indonesia", "method": "recovery"},
    {"name": "Lazada ID", "category": "Indonesia", "method": "recovery"},
    {"name": "JD.ID", "category": "Indonesia", "method": "recovery"},
    {"name": "Gojek", "category": "Indonesia", "method": "recovery"},
    {"name": "Grab ID", "category": "Indonesia", "method": "recovery"},
    {"name": "OVO", "category": "Indonesia", "method": "recovery"},
    {"name": "DANA", "category": "Indonesia", "method": "recovery"},
    {"name": "GoPay", "category": "Indonesia", "method": "recovery"},
    {"name": "LinkAja", "category": "Indonesia", "method": "recovery"},
    {"name": "Jenius", "category": "Indonesia", "method": "recovery"},
    {"name": "Traveloka", "category": "Indonesia", "method": "recovery"},
    {"name": "Tiket.com", "category": "Indonesia", "method": "recovery"},
]

# Developer & Tech
EMAIL_TECH = [
    {"name": "GitHub", "category": "Tech", "method": "recovery"},
    {"name": "GitLab", "category": "Tech", "method": "recovery"},
    {"name": "Bitbucket", "category": "Tech", "method": "recovery"},
    {"name": "Stack Overflow", "category": "Tech", "method": "recovery"},
    {"name": "Docker Hub", "category": "Tech", "method": "recovery"},
    {"name": "NPM", "category": "Tech", "method": "recovery"},
    {"name": "PyPI", "category": "Tech", "method": "recovery"},
    {"name": "Heroku", "category": "Tech", "method": "recovery"},
    {"name": "Vercel", "category": "Tech", "method": "recovery"},
    {"name": "Netlify", "category": "Tech", "method": "recovery"},
    {"name": "DigitalOcean", "category": "Tech", "method": "recovery"},
    {"name": "AWS", "category": "Tech", "method": "recovery"},
    {"name": "Google Cloud", "category": "Tech", "method": "recovery"},
    {"name": "Azure", "category": "Tech", "method": "recovery"},
    {"name": "Cloudflare", "category": "Tech", "method": "recovery"},
]

# Finance & Payment
EMAIL_FINANCE = [
    {"name": "PayPal", "category": "Finance", "method": "recovery"},
    {"name": "Stripe", "category": "Finance", "method": "recovery"},
    {"name": "Wise", "category": "Finance", "method": "recovery"},
    {"name": "Venmo", "category": "Finance", "method": "recovery"},
    {"name": "CashApp", "category": "Finance", "method": "recovery"},
    {"name": "Revolut", "category": "Finance", "method": "recovery"},
    {"name": "Coinbase", "category": "Crypto", "method": "recovery"},
    {"name": "Binance", "category": "Crypto", "method": "recovery"},
    {"name": "Kraken", "category": "Crypto", "method": "recovery"},
]

# Dating Apps
EMAIL_DATING = [
    {"name": "Tinder", "category": "Dating", "method": "recovery"},
    {"name": "Bumble", "category": "Dating", "method": "recovery"},
    {"name": "OkCupid", "category": "Dating", "method": "recovery"},
    {"name": "Hinge", "category": "Dating", "method": "recovery"},
    {"name": "Badoo", "category": "Dating", "method": "recovery"},
    {"name": "Match.com", "category": "Dating", "method": "recovery"},
    {"name": "Plenty of Fish", "category": "Dating", "method": "recovery"},
    {"name": "Coffee Meets Bagel", "category": "Dating", "method": "recovery"},
]

# Cloud & Productivity
EMAIL_CLOUD = [
    {"name": "Google", "category": "Cloud", "method": "recovery"},
    {"name": "Microsoft", "category": "Cloud", "method": "recovery"},
    {"name": "Apple", "category": "Cloud", "method": "recovery"},
    {"name": "Dropbox", "category": "Cloud", "method": "recovery"},
    {"name": "OneDrive", "category": "Cloud", "method": "recovery"},
    {"name": "iCloud", "category": "Cloud", "method": "recovery"},
    {"name": "Notion", "category": "Productivity", "method": "recovery"},
    {"name": "Evernote", "category": "Productivity", "method": "recovery"},
    {"name": "Trello", "category": "Productivity", "method": "recovery"},
    {"name": "Slack", "category": "Productivity", "method": "recovery"},
    {"name": "Zoom", "category": "Productivity", "method": "recovery"},
    {"name": "Canva", "category": "Productivity", "method": "recovery"},
    {"name": "Figma", "category": "Productivity", "method": "recovery"},
]

# Travel
EMAIL_TRAVEL = [
    {"name": "Airbnb", "category": "Travel", "method": "recovery"},
    {"name": "Booking.com", "category": "Travel", "method": "recovery"},
    {"name": "Expedia", "category": "Travel", "method": "recovery"},
    {"name": "Tripadvisor", "category": "Travel", "method": "recovery"},
    {"name": "Uber", "category": "Travel", "method": "recovery"},
    {"name": "Lyft", "category": "Travel", "method": "recovery"},
]

# Adult (optional)
EMAIL_ADULT = [
    {"name": "OnlyFans", "category": "Adult", "method": "recovery"},
    {"name": "Pornhub", "category": "Adult", "method": "recovery"},
]

# All platforms combined
ALL_EMAIL_PLATFORMS = (
    EMAIL_SOCIAL +
    EMAIL_STREAMING +
    EMAIL_GAMING +
    EMAIL_SHOPPING +
    EMAIL_INDONESIA +
    EMAIL_TECH +
    EMAIL_FINANCE +
    EMAIL_DATING +
    EMAIL_CLOUD +
    EMAIL_TRAVEL +
    EMAIL_ADULT
)

# Breach Check Services
BREACH_SERVICES = [
    {"name": "Have I Been Pwned", "url": "https://haveibeenpwned.com/account/{email}", "type": "Breach"},
    {"name": "XposedOrNot", "url": "https://xposedornot.com/result/{email}", "type": "Breach"},
    {"name": "DeHashed", "url": "https://www.dehashed.com/search?query={email}", "type": "Breach"},
    {"name": "Intelligence X", "url": "https://intelx.io/?s={email}", "type": "Breach"},
    {"name": "Leak-Lookup", "url": "https://leak-lookup.com/search?query={email}", "type": "Breach"},
    {"name": "BreachDirectory", "url": "https://breachdirectory.org/", "type": "Breach"},
    {"name": "Snusbase", "url": "https://snusbase.com/", "type": "Breach"},
    {"name": "LeakCheck", "url": "https://leakcheck.io/", "type": "Breach"},
]

# Email Verification Services
EMAIL_VERIFY_SERVICES = [
    {"name": "Hunter.io", "url": "https://hunter.io/email-verifier/{email}", "type": "Verify"},
    {"name": "EmailRep", "url": "https://emailrep.io/{email}", "type": "Reputation"},
    {"name": "Email Hippo", "url": "https://tools.emailhippo.com/email/{email}", "type": "Verify"},
    {"name": "Verify-Email", "url": "https://verify-email.org/email/{email}", "type": "Verify"},
    {"name": "Email Checker", "url": "https://email-checker.net/validate?email={email}", "type": "Verify"},
    {"name": "MailTester", "url": "https://mailtester.com/testmail.php?email={email}", "type": "Verify"},
]

# Google Dorks for Email
GOOGLE_DORKS_EMAIL = [
    {"name": "Exact Match", "query": '"{email}"'},
    {"name": "Username Part", "query": '"{username}"'},
    {"name": "Site LinkedIn", "query": 'site:linkedin.com "{email}"'},
    {"name": "Site Facebook", "query": 'site:facebook.com "{email}"'},
    {"name": "Site GitHub", "query": 'site:github.com "{email}"'},
    {"name": "PDF/Doc Files", "query": 'filetype:pdf OR filetype:doc "{email}"'},
    {"name": "Pastebin", "query": 'site:pastebin.com "{email}"'},
    {"name": "Contact Pages", "query": '"{email}" contact OR kontak'},
    {"name": "Data Breach", "query": '"{email}" breach OR leak OR dump'},
    {"name": "Database Dump", "query": '"{email}" database OR sql'},
]


class EmailOSINT(BaseScanner):
    """Ultimate Email OSINT scanner with 100+ platform checks."""
    
    def __init__(self, language: str = "id"):
        super().__init__("Email OSINT", language)
        self.xposedornot = XposedOrNotClient()
        self.http_client = APIClient()
    
    def scan(self, email: str, **options) -> Dict[str, Any]:
        """
        Comprehensive email OSINT scan.
        
        Args:
            email: Email address to scan
            scan_mode: 'quick' or 'deep'
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
            "breach_check_services": [],
            "email_verify_services": [],
            "platforms_to_check": [],
            "google_dorks": [],
            "gravatar": None,
            "disposable_check": {},
            "risk_assessment": {},
        }
        
        # 1. Domain analysis
        console.print("[cyan]→ Analyzing email domain...[/cyan]")
        results["domain_info"] = self._analyze_domain(domain)
        
        # 2. Breach check via API
        console.print("[cyan]→ Checking breach databases (API)...[/cyan]")
        breach_data = self._check_xposedornot(email)
        if breach_data:
            results["breaches"] = breach_data
        
        # 3. Generate breach check service links
        console.print("[cyan]→ Generating breach check links...[/cyan]")
        results["breach_check_services"] = self._generate_breach_links(email)
        
        # 4. Generate email verification links
        console.print("[cyan]→ Generating verification service links...[/cyan]")
        results["email_verify_services"] = self._generate_verify_links(email)
        
        # 5. Gravatar check
        console.print("[cyan]→ Checking Gravatar...[/cyan]")
        results["gravatar"] = self._check_gravatar(email)
        
        # 6. Disposable check
        console.print("[cyan]→ Checking if disposable email...[/cyan]")
        results["disposable_check"] = self._check_disposable(domain)
        
        # 7. Generate platform list to check
        if scan_mode == "deep":
            console.print("[cyan]→ Generating platform check list (100+ platforms)...[/cyan]")
            results["platforms_to_check"] = self._generate_platform_list(email, full=True)
        else:
            console.print("[cyan]→ Generating priority platform list...[/cyan]")
            results["platforms_to_check"] = self._generate_platform_list(email, full=False)
        
        # 8. Google dorks
        console.print("[cyan]→ Generating Google dork queries...[/cyan]")
        results["google_dorks"] = self._generate_google_dorks(email, username)
        
        # 9. Calculate risk
        results["risk_assessment"] = self._calculate_risk(results)
        
        # Summary stats
        results["total_platforms"] = len(results["platforms_to_check"])
        results["total_services"] = (
            len(results["breach_check_services"]) +
            len(results["email_verify_services"]) +
            len(results["google_dorks"])
        )
        
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
    
    def _generate_breach_links(self, email: str) -> List[Dict]:
        links = []
        for s in BREACH_SERVICES:
            links.append({
                "name": s["name"],
                "url": s["url"].replace("{email}", email),
                "type": s["type"],
            })
        return links
    
    def _generate_verify_links(self, email: str) -> List[Dict]:
        links = []
        for s in EMAIL_VERIFY_SERVICES:
            links.append({
                "name": s["name"],
                "url": s["url"].replace("{email}", email),
                "type": s["type"],
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
    
    def _generate_platform_list(self, email: str, full: bool = False) -> List[Dict]:
        """Generate list of platforms to manually check."""
        if full:
            platforms = ALL_EMAIL_PLATFORMS
        else:
            # Priority platforms only
            platforms = EMAIL_SOCIAL + EMAIL_TECH[:5] + EMAIL_INDONESIA[:5]
        
        # Categorize
        by_category = {}
        for p in platforms:
            cat = p["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(p["name"])
        
        result = []
        for cat, names in by_category.items():
            result.append({
                "category": cat,
                "platforms": names,
                "count": len(names),
                "note": "Check password recovery/forgot password page to see if email is registered",
            })
        
        return result
    
    def _generate_google_dorks(self, email: str, username: str) -> List[Dict]:
        dorks = []
        for d in GOOGLE_DORKS_EMAIL:
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
        
        level = "CRITICAL" if score >= 70 else "HIGH" if score >= 50 else "MEDIUM" if score >= 30 else "LOW"
        
        recommendations = []
        if results["breaches"]["found"]:
            recommendations.extend([
                "Change password immediately",
                "Enable 2FA",
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
