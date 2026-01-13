"""
CKSEARCH - Holehe Wrapper
===========================
Wrapper for Holehe email OSINT tool.
Checks registration status on 120+ sites.
"""

import asyncio
import sys
import inspect
from typing import Dict, Any, List

# Holehe imports
try:
    from holehe.core import import_submodules
except ImportError:
    pass

class HoleheWrapper:
    """Wrapper for Holehe library."""
    
    def __init__(self):
        self.modules = []
        try:
            # Import modules directory
            self.modules = import_submodules("holehe.modules")
        except:
            pass
            
    async def check_email(self, email: str) -> List[Dict]:
        """Check email against all Holehe modules."""
        if not self.modules:
            return []
            
        results = []
        import httpx
        
        # Use a timeout context
        async with httpx.AsyncClient(timeout=20) as client:
            out = []
            tasks = []
            
            for module in self.modules:
                if not hasattr(module, '__name__'):
                    continue
                    
                # Find the checker function in the module
                # It usually has the same name as the module or is the only async function
                # that isn't launch_module or maincore
                
                module_name = module.__name__.split('.')[-1]
                
                target_func = None
                
                # Method 1: Function with same name
                if hasattr(module, module_name):
                    func = getattr(module, module_name)
                    if inspect.iscoroutinefunction(func):
                        target_func = func
                
                # Method 2: Scan for async functions
                if not target_func:
                    for name in dir(module):
                        if name.startswith("_"): continue
                        attr = getattr(module, name)
                        if inspect.iscoroutinefunction(attr):
                            if name not in ["launch_module", "maincore"]:
                                target_func = attr
                                break
                
                if target_func:
                    tasks.append(self._safe_run(target_func, email, client, out))
            
            # Run all checks
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Format results
            for result in out:
                if not isinstance(result, dict):
                    continue
                    
                if result.get("exists"):
                    name = str(result.get("name", "Unknown"))
                    results.append({
                        "platform": name,
                        "category": self._categorize(name),
                        "exists": True,
                        "method": str(result.get("method", "holehe check")),
                        "details": str(result.get("others") or ""),
                        "rate_limit": result.get("rateLimit", False)
                    })
                    
        return results

    async def _safe_run(self, func, email, client, out):
        """Run a single module safely."""
        try:
            await func(email, client, out)
        except Exception:
            pass

    def _categorize(self, name: str) -> str:
        """Categorize platform based on name."""
        if not name:
            return "Other"
        
        name = name.lower()
        if any(x in name for x in ["twitter", "facebook", "instagram", "tiktok", "snapchat", "pinterest", "tumblr", "reddit"]):
            return "Social"
        if any(x in name for x in ["github", "gitlab", "bitbucket", "stackoverflow", "trello", "atlassian"]):
            return "Tech"
        if any(x in name for x in ["spotify", "deezer", "soundcloud", "last.fm", "apple"]):
            return "Music"
        if any(x in name for x in ["amazon", "ebay", "etsy", "aliexpress"]):
            return "Shopping"
        if any(x in name for x in ["linkedin", "freelancer", "upwork"]):
            return "Professional"
        if any(x in name for x in ["netflix", "hbo", "disney", "twitch"]):
            return "Entertainment"
        return "Other"

async def run_holehe(email: str) -> List[Dict]:
    wrapper = HoleheWrapper()
    return await wrapper.check_email(email)
