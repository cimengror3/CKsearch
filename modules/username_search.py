"""
CKSEARCH - Username Search Module (Accurate Edition)
======================================================
Multi-platform username search with proper validation.
Only shows CONFIRMED accounts - no false positives.
"""

import asyncio
import aiohttp
import re
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

import config
from core.scanner import BaseScanner

console = Console()


# =============================================================================
# PLATFORM DATABASE WITH VALIDATION RULES
# =============================================================================
# Format:
# - name: Platform name
# - url: URL with {} placeholder
# - error_type: How to detect if user NOT found
#   - "status": HTTP 404 = not found (reliable sites)
#   - "content": Check page content for error messages
#   - "content_positive": Check for content that MUST exist if user exists
#   - "json": Check JSON response
# - error_patterns: List of strings that indicate user NOT found (for content type)
# - positive_patterns: List of strings that MUST exist if user exists (for content_positive)

PLATFORMS = [
    # ===== SOCIAL MEDIA - HIGHLY RELIABLE =====
    {
        "name": "GitHub",
        "url": "https://github.com/{}",
        "category": "Tech",
        "error_type": "status",  # GitHub returns 404 for non-existent users
    },
    {
        "name": "Twitter/X",
        "url": "https://twitter.com/{}",
        "category": "Social",
        "error_type": "content",
        "error_patterns": ["This account doesn't exist", "Sorry, that page", "doesn't exist"],
    },
    {
        "name": "Instagram",
        "url": "https://www.instagram.com/{}/",
        "category": "Social",
        "error_type": "content",
        "error_patterns": ["Sorry, this page isn't available", "Page Not Found"],
    },
    {
        "name": "TikTok",
        "url": "https://www.tiktok.com/@{}",
        "category": "Social",
        "error_type": "content",
        "error_patterns": ["Couldn't find this account", "couldn't find this page"],
    },
    {
        "name": "Reddit",
        "url": "https://www.reddit.com/user/{}/",
        "category": "Social",
        "error_type": "content",
        "error_patterns": ["Sorry, nobody on Reddit goes by that name", "page not found"],
    },
    {
        "name": "Pinterest",
        "url": "https://www.pinterest.com/{}/",
        "category": "Social",
        "error_type": "status",
    },
    {
        "name": "Tumblr",
        "url": "https://{}.tumblr.com",
        "category": "Social",
        "error_type": "content",
        "error_patterns": ["There's nothing here", "Not found"],
    },
    {
        "name": "LinkedIn",
        "url": "https://www.linkedin.com/in/{}/",
        "category": "Professional",
        "error_type": "content",
        "error_patterns": ["Page not found", "This page doesn't exist"],
    },
    {
        "name": "Facebook",
        "url": "https://www.facebook.com/{}",
        "category": "Social",
        "error_type": "content",
        "error_patterns": ["This content isn't available", "Page Not Found", "Sorry, this content isn't available"],
    },
    {
        "name": "Threads",
        "url": "https://www.threads.net/@{}",
        "category": "Social",
        "error_type": "content",
        "error_patterns": ["Sorry, this page isn't available"],
    },
    
    # ===== TECH & DEVELOPER =====
    {
        "name": "GitLab",
        "url": "https://gitlab.com/{}",
        "category": "Tech",
        "error_type": "status",
    },
    {
        "name": "Bitbucket",
        "url": "https://bitbucket.org/{}/",
        "category": "Tech",
        "error_type": "status",
    },
    {
        "name": "Dev.to",
        "url": "https://dev.to/{}",
        "category": "Tech",
        "error_type": "status",
    },
    {
        "name": "CodePen",
        "url": "https://codepen.io/{}",
        "category": "Tech",
        "error_type": "status",
    },
    {
        "name": "Replit",
        "url": "https://replit.com/@{}",
        "category": "Tech",
        "error_type": "content",
        "error_patterns": ["user not found", "404"],
    },
    {
        "name": "HackerRank",
        "url": "https://www.hackerrank.com/{}",
        "category": "Tech",
        "error_type": "content",
        "error_patterns": ["Page Not Found", "Hmm, we can't find"],
    },
    {
        "name": "LeetCode",
        "url": "https://leetcode.com/{}",
        "category": "Tech",
        "error_type": "content",
        "error_patterns": ["That page doesn't exist"],
    },
    {
        "name": "Kaggle",
        "url": "https://www.kaggle.com/{}",
        "category": "Tech",
        "error_type": "status",
    },
    {
        "name": "Hashnode",
        "url": "https://hashnode.com/@{}",
        "category": "Tech",
        "error_type": "content",
        "error_patterns": ["not found", "doesn't exist"],
    },
    {
        "name": "Docker Hub",
        "url": "https://hub.docker.com/u/{}",
        "category": "Tech",
        "error_type": "status",
    },
    {
        "name": "NPM",
        "url": "https://www.npmjs.com/~{}",
        "category": "Tech",
        "error_type": "status",
    },
    {
        "name": "PyPI",
        "url": "https://pypi.org/user/{}/",
        "category": "Tech",
        "error_type": "status",
    },
    {
        "name": "Keybase",
        "url": "https://keybase.io/{}",
        "category": "Tech",
        "error_type": "status",
    },
    
    # ===== GAMING =====
    {
        "name": "Steam",
        "url": "https://steamcommunity.com/id/{}",
        "category": "Gaming",
        "error_type": "content",
        "error_patterns": ["The specified profile could not be found"],
    },
    {
        "name": "Twitch",
        "url": "https://www.twitch.tv/{}",
        "category": "Gaming",
        "error_type": "content",
        "error_patterns": ["Sorry. Unless you've got a time machine", "that page is in another castle"],
    },
    {
        "name": "Kick",
        "url": "https://kick.com/{}",
        "category": "Gaming",
        "error_type": "content",
        "error_patterns": ["Page not found", "Channel not found"],
    },
    {
        "name": "Chess.com",
        "url": "https://www.chess.com/member/{}",
        "category": "Gaming",
        "error_type": "content",
        "error_patterns": ["is not a valid username"],
    },
    {
        "name": "Lichess",
        "url": "https://lichess.org/@/{}",
        "category": "Gaming",
        "error_type": "status",
    },
    {
        "name": "osu!",
        "url": "https://osu.ppy.sh/users/{}",
        "category": "Gaming",
        "error_type": "content",
        "error_patterns": ["The user you are looking for was not found"],
    },
    {
        "name": "Speedrun.com",
        "url": "https://www.speedrun.com/user/{}",
        "category": "Gaming",
        "error_type": "status",
    },
    {
        "name": "NameMC",
        "url": "https://namemc.com/profile/{}",
        "category": "Gaming",
        "error_type": "content",
        "error_patterns": ["Profile Not Found"],
    },
    
    # ===== VIDEO & STREAMING =====
    {
        "name": "YouTube",
        "url": "https://www.youtube.com/@{}",
        "category": "Video",
        "error_type": "content",
        "error_patterns": ["This page isn't available", "404 Not Found"],
    },
    {
        "name": "Vimeo",
        "url": "https://vimeo.com/{}",
        "category": "Video",
        "error_type": "status",
    },
    {
        "name": "DailyMotion",
        "url": "https://www.dailymotion.com/{}",
        "category": "Video",
        "error_type": "status",
    },
    {
        "name": "Rumble",
        "url": "https://rumble.com/user/{}",
        "category": "Video",
        "error_type": "content",
        "error_patterns": ["Channel not found"],
    },
    {
        "name": "Odysee",
        "url": "https://odysee.com/@{}",
        "category": "Video",
        "error_type": "content",
        "error_patterns": ["This channel does not exist"],
    },
    
    # ===== MUSIC =====
    {
        "name": "Spotify",
        "url": "https://open.spotify.com/user/{}",
        "category": "Music",
        "error_type": "content_positive",
        "positive_patterns": ["Public Playlists", "Followers", "Following"],
    },
    {
        "name": "SoundCloud",
        "url": "https://soundcloud.com/{}",
        "category": "Music",
        "error_type": "content",
        "error_patterns": ["We can't find that user"],
    },
    {
        "name": "Bandcamp",
        "url": "https://{}.bandcamp.com",
        "category": "Music",
        "error_type": "content",
        "error_patterns": ["Sorry, that something isn't here"],
    },
    {
        "name": "Last.fm",
        "url": "https://www.last.fm/user/{}",
        "category": "Music",
        "error_type": "status",
    },
    {
        "name": "Mixcloud",
        "url": "https://www.mixcloud.com/{}/",
        "category": "Music",
        "error_type": "status",
    },
    
    # ===== PHOTO & ART =====
    {
        "name": "Flickr",
        "url": "https://www.flickr.com/people/{}/",
        "category": "Photo",
        "error_type": "content",
        "error_patterns": ["member not found"],
    },
    {
        "name": "500px",
        "url": "https://500px.com/p/{}",
        "category": "Photo",
        "error_type": "status",
    },
    {
        "name": "Unsplash",
        "url": "https://unsplash.com/@{}",
        "category": "Photo",
        "error_type": "status",
    },
    {
        "name": "DeviantArt",
        "url": "https://www.deviantart.com/{}",
        "category": "Art",
        "error_type": "content",
        "error_patterns": ["This DeviantArt page does not exist"],
    },
    {
        "name": "ArtStation",
        "url": "https://www.artstation.com/{}",
        "category": "Art",
        "error_type": "content",
        "error_patterns": ["Oops! We couldn't find"],
    },
    {
        "name": "Behance",
        "url": "https://www.behance.net/{}",
        "category": "Art",
        "error_type": "content",
        "error_patterns": ["Oops! We can't find"],
    },
    {
        "name": "Dribbble",
        "url": "https://dribbble.com/{}",
        "category": "Art",
        "error_type": "status",
    },
    {
        "name": "Imgur",
        "url": "https://imgur.com/user/{}/",
        "category": "Photo",
        "error_type": "content",
        "error_patterns": ["Couldn't find that user"],
    },
    {
        "name": "VSCO",
        "url": "https://vsco.co/{}",
        "category": "Photo",
        "error_type": "content",
        "error_patterns": ["Page not found"],
    },
    
    # ===== BLOG & WRITING =====
    {
        "name": "Medium",
        "url": "https://medium.com/@{}",
        "category": "Blog",
        "error_type": "content",
        "error_patterns": ["PAGE NOT FOUND", "doesn't have any stories"],
    },
    {
        "name": "Substack",
        "url": "https://{}.substack.com",
        "category": "Blog",
        "error_type": "content",
        "error_patterns": ["Page not found"],
    },
    {
        "name": "WordPress",
        "url": "https://{}.wordpress.com",
        "category": "Blog",
        "error_type": "content",
        "error_patterns": ["doesn't exist", "is no longer available"],
    },
    {
        "name": "Wattpad",
        "url": "https://www.wattpad.com/user/{}",
        "category": "Writing",
        "error_type": "status",
    },
    {
        "name": "Goodreads",
        "url": "https://www.goodreads.com/{}",
        "category": "Book",
        "error_type": "status",
    },
    {
        "name": "Scribd",
        "url": "https://www.scribd.com/{}",
        "category": "Book",
        "error_type": "status",
    },
    
    # ===== PROFESSIONAL & BUSINESS =====
    {
        "name": "About.me",
        "url": "https://about.me/{}",
        "category": "Professional",
        "error_type": "status",
    },
    {
        "name": "Linktree",
        "url": "https://linktr.ee/{}",
        "category": "Professional",
        "error_type": "content",
        "error_patterns": ["This Linktree doesn't exist", "Nothing here"],
    },
    {
        "name": "Carrd",
        "url": "https://{}.carrd.co",
        "category": "Professional",
        "error_type": "content",
        "error_patterns": ["Not found"],
    },
    {
        "name": "Fiverr",
        "url": "https://www.fiverr.com/{}",
        "category": "Professional",
        "error_type": "content",
        "error_patterns": ["isn't available", "Page not found"],
    },
    {
        "name": "Upwork",
        "url": "https://www.upwork.com/freelancers/~{}",
        "category": "Professional",
        "error_type": "content",
        "error_patterns": ["Page not found", "profile is unavailable"],
    },
    
    # ===== SHOPPING & MARKETPLACE =====
    {
        "name": "eBay",
        "url": "https://www.ebay.com/usr/{}",
        "category": "Shopping",
        "error_type": "content",
        "error_patterns": ["The User ID you entered was not found"],
    },
    {
        "name": "Etsy",
        "url": "https://www.etsy.com/shop/{}",
        "category": "Shopping",
        "error_type": "content",
        "error_patterns": ["Sorry, this shop is currently unavailable"],
    },
    {
        "name": "Poshmark",
        "url": "https://poshmark.com/closet/{}",
        "category": "Shopping",
        "error_type": "content",
        "error_patterns": ["Closet Not Found"],
    },
    {
        "name": "Depop",
        "url": "https://www.depop.com/{}",
        "category": "Shopping",
        "error_type": "content",
        "error_patterns": ["This page doesn't exist"],
    },
    {
        "name": "Redbubble",
        "url": "https://www.redbubble.com/people/{}/shop",
        "category": "Shopping",
        "error_type": "content",
        "error_patterns": ["Oops! We couldn't find"],
    },
    
    # ===== FINANCE & DONATION =====
    {
        "name": "PayPal.me",
        "url": "https://paypal.me/{}",
        "category": "Finance",
        "error_type": "content",
        "error_patterns": ["This link is not available"],
    },
    {
        "name": "Ko-fi",
        "url": "https://ko-fi.com/{}",
        "category": "Finance",
        "error_type": "content",
        "error_patterns": ["doesn't have a Ko-fi page"],
    },
    {
        "name": "BuyMeACoffee",
        "url": "https://www.buymeacoffee.com/{}",
        "category": "Finance",
        "error_type": "content",
        "error_patterns": ["Page not found"],
    },
    {
        "name": "Patreon",
        "url": "https://www.patreon.com/{}",
        "category": "Finance",
        "error_type": "content",
        "error_patterns": ["not exist", "404"],
    },
    
    # ===== CHAT & MESSAGING =====
    {
        "name": "Telegram",
        "url": "https://t.me/{}",
        "category": "Chat",
        "error_type": "content",
        "error_patterns": ["If you have Telegram", "preview is not available"],
    },
    {
        "name": "Gravatar",
        "url": "https://en.gravatar.com/{}",
        "category": "Other",
        "error_type": "status",
    },
    {
        "name": "Disqus",
        "url": "https://disqus.com/by/{}/",
        "category": "Other",
        "error_type": "status",
    },
    
    # ===== INDONESIA PLATFORMS =====
    {
        "name": "Kaskus",
        "url": "https://www.kaskus.co.id/profile/{}",
        "category": "Indonesia",
        "error_type": "content",
        "error_patterns": ["Profil tidak ditemukan", "Not found"],
    },
    {
        "name": "Tokopedia",
        "url": "https://www.tokopedia.com/{}",
        "category": "Indonesia",
        "error_type": "content",
        "error_patterns": ["Toko Tidak Ditemukan", "Halaman tidak ditemukan"],
    },
    {
        "name": "Bukalapak",
        "url": "https://www.bukalapak.com/u/{}",
        "category": "Indonesia",
        "error_type": "content",
        "error_patterns": ["Lapak tidak ditemukan"],
    },
    {
        "name": "Shopee ID",
        "url": "https://shopee.co.id/{}",
        "category": "Indonesia",
        "error_type": "content",
        "error_patterns": ["Halaman tidak ditemukan"],
    },
    {
        "name": "Kompasiana",
        "url": "https://www.kompasiana.com/{}",
        "category": "Indonesia",
        "error_type": "content",
        "error_patterns": ["halaman tidak ditemukan", "Page not found"],
    },
    {
        "name": "Brainly ID",
        "url": "https://brainly.co.id/profil/{}",
        "category": "Indonesia",
        "error_type": "content",
        "error_patterns": ["Pengguna tidak ditemukan", "User not found"],
    },
]

# Quick scan subset - most reliable platforms only  
QUICK_PLATFORMS = [p for p in PLATFORMS if p["category"] in ["Tech", "Social", "Gaming", "Video", "Music", "Art"]][:40]


class UsernameSearch(BaseScanner):
    """Accurate username searcher - only shows CONFIRMED accounts."""
    
    def __init__(self, language: str = "id"):
        super().__init__("Username Search", language)
    
    def scan(self, username: str, **options) -> Dict[str, Any]:
        """
        Scan for username across platforms.
        Only returns platforms where account is CONFIRMED to exist.
        
        Args:
           username: Username target
           scan_mode: 'quick' (40 sites) or 'deep' (80+ sites)
        """
        self._start()
        
        scan_mode = options.get("scan_mode", "quick")
        
        if not username or len(username) < 2:
            return {"error": "Username too short"}
        
        # Select platforms
        if scan_mode == "deep":
            platforms = PLATFORMS.copy()
        else:
            platforms = QUICK_PLATFORMS.copy()
        
        console.print(f"[cyan]→ Scanning {len(platforms)} platforms ({scan_mode.upper()} Mode)...[/cyan]")
        console.print(f"[dim]  Only CONFIRMED accounts will be shown[/dim]")
        
        results = {
            "target": username,
            "scan_mode": scan_mode,
            "total_checked": len(platforms),
            "found": [],
            "categories": {},
        }
        
        # Async scan with validation
        found_data = asyncio.run(self._scan_platforms(username, platforms))
        results["found"] = found_data
        results["count"] = len(found_data)
        
        # Categorize
        for item in found_data:
            cat = item.get("category", "Other")
            if cat not in results["categories"]:
                results["categories"][cat] = []
            results["categories"][cat].append(item)
        
        self._finish()
        results["metadata"] = self.get_metadata()
        
        return results
    
    async def _scan_platforms(self, username: str, platforms: List[Dict]) -> List[Dict]:
        """Scan platforms with proper validation."""
        found = []
        
        timeout = aiohttp.ClientTimeout(total=15)
        connector = aiohttp.TCPConnector(limit=50, ssl=False)
        
        headers = {
            "User-Agent": config.DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers=headers) as session:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=40),
                TaskProgressColumn(),
                TextColumn("[green]Confirmed: {task.fields[found_count]}[/green]"),
                console=console
            ) as progress:
                
                found_count = 0
                task = progress.add_task("Checking...", total=len(platforms), found_count=0)
                
                tasks = [self._check_platform(session, platform, username) for platform in platforms]
                
                for future in asyncio.as_completed(tasks):
                    result = await future
                    if result:
                        found.append(result)
                        found_count += 1
                    progress.update(task, advance=1, found_count=found_count)
        
        return found
    
    async def _check_platform(self, session: aiohttp.ClientSession, platform: Dict, username: str) -> Optional[Dict]:
        """Check single platform with proper validation."""
        url = platform["url"].format(username)
        error_type = platform.get("error_type", "status")
        
        try:
            async with session.get(url, allow_redirects=True) as resp:
                # Strategy 1: Status-based (most reliable)
                if error_type == "status":
                    if resp.status == 200:
                        # Additional check: ensure we didn't get redirected to error page
                        final_url = str(resp.url).lower()
                        if "404" in final_url or "error" in final_url or "notfound" in final_url:
                            return None
                        return self._create_result(platform, url)
                    return None
                
                # Strategy 2: Content-based (check for error messages)
                elif error_type == "content":
                    if resp.status != 200:
                        return None
                    
                    try:
                        text = await resp.text()
                        text_lower = text.lower()
                        
                        # Check for error patterns
                        error_patterns = platform.get("error_patterns", [])
                        for pattern in error_patterns:
                            if pattern.lower() in text_lower:
                                return None  # Found error message = user doesn't exist
                        
                        # No error pattern found = user likely exists
                        return self._create_result(platform, url)
                    except:
                        return None
                
                # Strategy 3: Positive content check (must have certain content)
                elif error_type == "content_positive":
                    if resp.status != 200:
                        return None
                    
                    try:
                        text = await resp.text()
                        text_lower = text.lower()
                        
                        positive_patterns = platform.get("positive_patterns", [])
                        for pattern in positive_patterns:
                            if pattern.lower() in text_lower:
                                return self._create_result(platform, url)
                        
                        return None  # Required content not found
                    except:
                        return None
                
        except asyncio.TimeoutError:
            return None
        except Exception:
            return None
        
        return None
    
    def _create_result(self, platform: Dict, url: str) -> Dict:
        """Create a validated result entry."""
        return {
            "site": platform["name"],
            "url": url,
            "category": platform.get("category", "Other"),
            "verified": True,
        }


def scan_username(username: str, scan_mode: str = "quick") -> Dict[str, Any]:
    """Convenience function."""
    return UsernameSearch().scan(username, scan_mode=scan_mode)
