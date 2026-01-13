"""
CKSEARCH - Maigret Wrapper
==========================
Wrapper for Maigret username OSINT tool.
Checks registration status on 3000+ sites.
"""

import asyncio
import logging
from typing import Dict, Any, List

try:
    from maigret import MaigretDatabase, MaigretEngine
    HAS_MAIGRET = True
except ImportError:
    HAS_MAIGRET = False

# Suppress Maigret logs
logging.getLogger("maigret").setLevel(logging.ERROR)

class MaigretWrapper:
    """Wrapper for Maigret library."""
    
    def __init__(self):
        self.db = None
        if HAS_MAIGRET:
            try:
                self.db = MaigretDatabase().load_from_file(None)
            except:
                pass
            
    async def check_username(self, username: str, scan_mode: str = "quick") -> List[Dict]:
        """Check username against Maigret database."""
        if not HAS_MAIGRET or not self.db:
            return []
            
        results = []
        
        # Select sites based on mode
        sites = self.db.sites
        
        if scan_mode == "quick":
            sites = sites[:50]
        else:
            sites = sites[:200]
            
        try:
            engine = MaigretEngine()
            
            # Use Maigret's concurrent execution logic manually to have control
            tasks = {}
            for site in sites:
                tasks[site.name] = engine.site_search_username(
                    username=username,
                    site=site,
                    timeout=10,
                    id_type="username"
                )
            
            responses = await asyncio.gather(*tasks.values(), return_exceptions=True)
            
            for i, result in enumerate(responses):
                site_name = sites[i].name
                
                if isinstance(result, Exception):
                    continue
                    
                if not result:
                    continue
                
                # Check status safe way (string repr)
                status = result.get("status")
                
                # Maigret 0.5.0 usually returns QueryStatus.CLAIMED for found accounts
                if status and "CLAIMED" in str(status):
                    results.append({
                        "site": site_name,
                        "url": result.get("url_user", ""),
                        "category": self._categorize(site_name),
                        "verified": True
                    })
                    
        except Exception:
            pass
            
        return results

    def _categorize(self, name: str) -> str:
        name = name.lower()
        if any(x in name for x in ["adult", "porn", "cam", "sex"]):
            return "Adult"
        if any(x in name for x in ["hack", "security", "exploit", "crack"]):
            return "Hacking"
        if any(x in name for x in ["game", "steam", "twitch", "xbox", "psn"]):
            return "Gaming"
        if any(x in name for x in ["code", "git", "dev", "tech", "stack"]):
            return "Tech"
        if any(x in name for x in ["insta", "face", "twitter", "tiktok", "social"]):
            return "Social"
        return "General"

async def run_maigret(username: str, scan_mode: str = "quick") -> List[Dict]:
    wrapper = MaigretWrapper()
    return await wrapper.check_username(username, scan_mode)
