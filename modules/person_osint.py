"""
CKSEARCH - Person OSINT Module
===============================
Person/name-based intelligence gathering.
"""

import re
from typing import Dict, Any, List
from rich.console import Console

import config
from core.scanner import BaseScanner
from core.api_client import APIClient

console = Console()


class PersonOSINT(BaseScanner):
    """Person OSINT scanner for name-based searches."""
    
    def __init__(self, language: str = "id"):
        super().__init__("Person OSINT", language)
        self.http_client = APIClient()
    
    def scan(self, name: str, **options) -> Dict[str, Any]:
        """
        Search for person by name.
        
        Args:
            name: Full name to search
            location: Optional location to narrow search
        """
        self._start()
        
        location = options.get("location", "")
        
        results = {
            "name": name,
            "location": location,
            "search_queries": {},
            "possible_usernames": [],
            "social_media_search": [],
            "professional_search": [],
            "public_records_search": [],
            "search_engines": [],
        }
        
        # Generate possible usernames
        console.print("[cyan]→ Generating possible usernames...[/cyan]")
        results["possible_usernames"] = self._generate_usernames(name)
        
        # Generate search queries
        console.print("[cyan]→ Generating search queries...[/cyan]")
        results["search_queries"] = self._generate_search_queries(name, location)
        
        # Social media search URLs
        console.print("[cyan]→ Generating social media search links...[/cyan]")
        results["social_media_search"] = self._generate_social_searches(name)
        
        # Professional network searches
        console.print("[cyan]→ Generating professional search links...[/cyan]")
        results["professional_search"] = self._generate_professional_searches(name, location)
        
        # Public records
        console.print("[cyan]→ Generating public records search links...[/cyan]")
        results["public_records_search"] = self._generate_public_records_searches(name, location)
        
        # Search engines
        results["search_engines"] = self._generate_search_engine_links(name, location)
        
        results["recommendations"] = [
            "Use generated usernames with Username Search module",
            "Cross-reference results across multiple platforms",
            "Verify identity before drawing conclusions",
        ]
        
        self._finish()
        results["metadata"] = self.get_metadata()
        return results
    
    def _generate_usernames(self, name: str) -> List[str]:
        """Generate possible usernames from name."""
        parts = name.lower().split()
        if len(parts) < 2:
            return [name.lower().replace(" ", "")]
        
        first = parts[0]
        last = parts[-1]
        initials = "".join(p[0] for p in parts)
        
        patterns = [
            f"{first}{last}",
            f"{first}.{last}",
            f"{first}_{last}",
            f"{first[0]}{last}",
            f"{first}{last[0]}",
            f"{last}{first}",
            f"{initials}",
            f"{first}{last}123",
            f"{first}.{last}.{last}",
            f"{last}.{first}",
        ]
        
        return list(set(patterns))
    
    def _generate_search_queries(self, name: str, location: str = "") -> Dict[str, str]:
        """Generate Google dork queries."""
        queries = {
            "exact_name": f'"{name}"',
            "with_location": f'"{name}" "{location}"' if location else None,
            "linkedin": f'site:linkedin.com "{name}"',
            "facebook": f'site:facebook.com "{name}"',
            "twitter": f'site:twitter.com "{name}"',
            "instagram": f'site:instagram.com "{name}"',
            "resume": f'"{name}" filetype:pdf resume OR cv',
            "documents": f'"{name}" filetype:pdf OR filetype:doc',
            "news": f'"{name}" site:news.google.com',
            "images": f'"{name}" site:images.google.com',
        }
        return {k: v for k, v in queries.items() if v}
    
    def _generate_social_searches(self, name: str) -> List[Dict[str, str]]:
        """Generate social media search URLs."""
        encoded = name.replace(" ", "%20")
        plus_encoded = name.replace(" ", "+")
        
        return [
            {"platform": "Facebook", "url": f"https://www.facebook.com/search/people/?q={encoded}"},
            {"platform": "Twitter/X", "url": f"https://twitter.com/search?q={encoded}&f=user"},
            {"platform": "Instagram", "url": f"https://www.instagram.com/explore/tags/{name.replace(' ', '')}"},
            {"platform": "LinkedIn", "url": f"https://www.linkedin.com/search/results/people/?keywords={encoded}"},
            {"platform": "TikTok", "url": f"https://www.tiktok.com/search/user?q={encoded}"},
            {"platform": "Pinterest", "url": f"https://www.pinterest.com/search/users/?q={encoded}"},
            {"platform": "YouTube", "url": f"https://www.youtube.com/results?search_query={plus_encoded}"},
            {"platform": "Reddit", "url": f"https://www.reddit.com/search/?q={encoded}&type=user"},
            {"platform": "GitHub", "url": f"https://github.com/search?q={encoded}&type=users"},
        ]
    
    def _generate_professional_searches(self, name: str, location: str = "") -> List[Dict[str, str]]:
        """Generate professional network search URLs."""
        encoded = name.replace(" ", "%20")
        
        searches = [
            {"platform": "LinkedIn", "url": f"https://www.linkedin.com/search/results/people/?keywords={encoded}"},
            {"platform": "Crunchbase", "url": f"https://www.crunchbase.com/textsearch?q={encoded}"},
            {"platform": "AngelList", "url": f"https://angel.co/search?q={encoded}"},
            {"platform": "GitHub", "url": f"https://github.com/search?q={encoded}&type=users"},
            {"platform": "ResearchGate", "url": f"https://www.researchgate.net/search/researcher?q={encoded}"},
            {"platform": "Google Scholar", "url": f"https://scholar.google.com/citations?view_op=search_authors&mauthors={encoded}"},
        ]
        return searches
    
    def _generate_public_records_searches(self, name: str, location: str = "") -> List[Dict[str, str]]:
        """Generate public records search URLs."""
        encoded = name.replace(" ", "+")
        
        return [
            {"source": "WhitePages", "url": f"https://www.whitepages.com/name/{encoded}"},
            {"source": "Spokeo", "url": f"https://www.spokeo.com/search?q={encoded}"},
            {"source": "BeenVerified", "url": f"https://www.beenverified.com/people/{encoded}/"},
            {"source": "Pipl", "url": f"https://pipl.com/search/?q={encoded}"},
            {"source": "That's Them", "url": f"https://thatsthem.com/name/{encoded}"},
            {"source": "FastPeopleSearch", "url": f"https://www.fastpeoplesearch.com/name/{encoded}"},
        ]
    
    def _generate_search_engine_links(self, name: str, location: str = "") -> List[Dict[str, str]]:
        """Generate search engine URLs."""
        q = f"{name} {location}".strip() if location else name
        encoded = q.replace(" ", "+")
        
        return [
            {"engine": "Google", "url": f"https://www.google.com/search?q={encoded}"},
            {"engine": "Bing", "url": f"https://www.bing.com/search?q={encoded}"},
            {"engine": "DuckDuckGo", "url": f"https://duckduckgo.com/?q={encoded}"},
            {"engine": "Yandex", "url": f"https://yandex.com/search/?text={encoded}"},
            {"engine": "Google Images", "url": f"https://www.google.com/search?q={encoded}&tbm=isch"},
        ]


def search_person(name: str, location: str = "") -> Dict[str, Any]:
    """Quick person search function."""
    return PersonOSINT().scan(name, location=location)
