"""
CKSEARCH - Social Media Deep Scan Module
==========================================
Deep analysis of social media profiles.
"""

import re
from typing import Dict, Any, List, Optional
from rich.console import Console

import config
from core.scanner import BaseScanner
from core.api_client import APIClient

console = Console()


class SocialDeepScan(BaseScanner):
    """Deep scan social media profiles."""
    
    def __init__(self, language: str = "id"):
        super().__init__("Social Deep Scan", language)
        self.http_client = APIClient()
    
    def scan(self, profile_url: str, **options) -> Dict[str, Any]:
        """
        Deep scan a social media profile.
        
        Args:
            profile_url: URL to social media profile
        """
        self._start()
        
        # Detect platform
        platform = self._detect_platform(profile_url)
        
        results = {
            "profile_url": profile_url,
            "platform": platform,
            "username": self._extract_username(profile_url, platform),
            "profile_data": {},
            "analysis": {},
            "osint_links": [],
            "archive_links": [],
        }
        
        if not platform:
            self._add_warning("Could not detect platform")
        
        # Get profile data based on platform
        console.print(f"[cyan]→ Analyzing {platform or 'unknown'} profile...[/cyan]")
        results["profile_data"] = self._scrape_profile(profile_url, platform)
        
        # Generate OSINT links
        console.print("[cyan]→ Generating OSINT research links...[/cyan]")
        results["osint_links"] = self._generate_osint_links(results["username"], platform)
        
        # Archive links
        console.print("[cyan]→ Generating archive links...[/cyan]")
        results["archive_links"] = self._generate_archive_links(profile_url)
        
        # Analysis
        results["analysis"] = self._analyze_profile(results)
        
        self._finish()
        results["metadata"] = self.get_metadata()
        return results
    
    def _detect_platform(self, url: str) -> Optional[str]:
        """Detect social media platform from URL."""
        platforms = {
            'instagram.com': 'Instagram',
            'twitter.com': 'Twitter',
            'x.com': 'Twitter',
            'facebook.com': 'Facebook',
            'linkedin.com': 'LinkedIn',
            'tiktok.com': 'TikTok',
            'youtube.com': 'YouTube',
            'github.com': 'GitHub',
            'reddit.com': 'Reddit',
            'pinterest.com': 'Pinterest',
            'twitch.tv': 'Twitch',
            'threads.net': 'Threads',
            'mastodon.social': 'Mastodon',
            'tumblr.com': 'Tumblr',
            't.me': 'Telegram',
        }
        
        for domain, platform in platforms.items():
            if domain in url.lower():
                return platform
        return None
    
    def _extract_username(self, url: str, platform: str = None) -> Optional[str]:
        """Extract username from profile URL."""
        patterns = {
            'Instagram': r'instagram\.com/([^/?]+)',
            'Twitter': r'(?:twitter|x)\.com/([^/?]+)',
            'Facebook': r'facebook\.com/([^/?]+)',
            'LinkedIn': r'linkedin\.com/in/([^/?]+)',
            'TikTok': r'tiktok\.com/@?([^/?]+)',
            'YouTube': r'youtube\.com/(?:@|user/|c/)?([^/?]+)',
            'GitHub': r'github\.com/([^/?]+)',
            'Reddit': r'reddit\.com/(?:user|u)/([^/?]+)',
        }
        
        pattern = patterns.get(platform)
        if pattern:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Generic fallback
        parts = url.rstrip('/').split('/')
        return parts[-1] if parts else None
    
    def _scrape_profile(self, url: str, platform: str) -> Dict[str, Any]:
        """Attempt to scrape public profile data."""
        data = {
            "accessible": False,
            "public": None,
        }
        
        try:
            response = self.http_client.session.get(url, timeout=15)
            data["accessible"] = response.status_code == 200
            
            if response.status_code == 200:
                html = response.text
                
                # Try to extract basic info from HTML
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                # Get title
                title = soup.find('title')
                if title:
                    data["page_title"] = title.text.strip()
                
                # Get meta description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    data["description"] = meta_desc.get('content', '')
                
                # OG data
                og_image = soup.find('meta', attrs={'property': 'og:image'})
                if og_image:
                    data["profile_image"] = og_image.get('content')
                
                og_title = soup.find('meta', attrs={'property': 'og:title'})
                if og_title:
                    data["display_name"] = og_title.get('content')
                
                data["public"] = True
                
            elif response.status_code == 404:
                data["note"] = "Profile not found or private"
                
        except Exception as e:
            data["error"] = str(e)
        
        return data
    
    def _generate_osint_links(self, username: str, platform: str) -> List[Dict[str, str]]:
        """Generate OSINT research links."""
        if not username:
            return []
        
        links = [
            {"tool": "Wayback Machine", "url": f"https://web.archive.org/web/*/{platform.lower()}.com/{username}"},
            {"tool": "Cached Pages", "url": f"https://webcache.googleusercontent.com/search?q=cache:{platform.lower()}.com/{username}"},
            {"tool": "Google Search", "url": f"https://www.google.com/search?q=\"{username}\"+site:{platform.lower()}.com"},
        ]
        
        # Platform specific
        if platform == "Instagram":
            links.extend([
                {"tool": "StoriesIG", "url": f"https://storiesig.info/en/stories/{username}"},
                {"tool": "Picuki", "url": f"https://www.picuki.com/profile/{username}"},
            ])
        elif platform == "Twitter":
            links.extend([
                {"tool": "Nitter", "url": f"https://nitter.net/{username}"},
                {"tool": "TweetDeck Search", "url": f"https://twitter.com/search?q=from:{username}"},
                {"tool": "Twitter Analytics", "url": f"https://socialblade.com/twitter/user/{username}"},
            ])
        elif platform == "TikTok":
            links.extend([
                {"tool": "TikTok Analytics", "url": f"https://socialblade.com/tiktok/user/{username}"},
            ])
        elif platform == "YouTube":
            links.extend([
                {"tool": "Social Blade", "url": f"https://socialblade.com/youtube/user/{username}"},
            ])
        elif platform == "GitHub":
            links.extend([
                {"tool": "GitHub Stats", "url": f"https://github-readme-stats.vercel.app/api?username={username}"},
                {"tool": "GitHub Contributions", "url": f"https://github.com/{username}?tab=repositories"},
            ])
        
        return links
    
    def _generate_archive_links(self, url: str) -> List[Dict[str, str]]:
        """Generate archive and cached version links."""
        encoded = url.replace(":", "%3A").replace("/", "%2F")
        
        return [
            {"service": "Wayback Machine", "url": f"https://web.archive.org/web/*/{url}"},
            {"service": "Archive.today", "url": f"https://archive.today/{url}"},
            {"service": "Google Cache", "url": f"https://webcache.googleusercontent.com/search?q=cache:{url}"},
            {"service": "Bing Cache", "url": f"https://cc.bingj.com/cache.aspx?q={encoded}"},
        ]
    
    def _analyze_profile(self, results: Dict) -> Dict[str, Any]:
        """Analyze profile data."""
        analysis = {
            "recommendations": [],
            "found_data": [],
        }
        
        profile_data = results.get("profile_data", {})
        
        if profile_data.get("accessible"):
            analysis["found_data"].append("Profile is publicly accessible")
        
        if profile_data.get("display_name"):
            analysis["found_data"].append(f"Display name: {profile_data['display_name']}")
        
        if profile_data.get("description"):
            analysis["found_data"].append(f"Bio/description found")
        
        if profile_data.get("profile_image"):
            analysis["found_data"].append("Profile image URL extracted")
            analysis["recommendations"].append("Use reverse image search on profile picture")
        
        username = results.get("username")
        if username:
            analysis["recommendations"].extend([
                f"Search username '{username}' across other platforms",
                "Check archived versions for historical data",
                "Analyze connected accounts and mentions",
            ])
        
        return analysis


def deep_scan_social(url: str) -> Dict[str, Any]:
    """Quick social media deep scan function."""
    return SocialDeepScan().scan(url)
