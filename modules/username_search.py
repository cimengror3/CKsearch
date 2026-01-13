"""
CKSEARCH - Username Search Module (Powered by Maigret)
======================================================
Multi-platform username search using Maigret engine.
Checks 3000+ sites with high accuracy.
"""

import asyncio
from typing import Dict, Any, List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from core.scanner import BaseScanner
from core.maigret_wrapper import run_maigret, HAS_MAIGRET

console = Console()

class UsernameSearch(BaseScanner):
    """Username searcher powered by Maigret."""
    
    def __init__(self, language: str = "id"):
        super().__init__("Username Search", language)
    
    def scan(self, username: str, **options) -> Dict[str, Any]:
        """
        Scan for username across platforms using Maigret.
        
        Args:
           username: Username target
           scan_mode: 'quick' (Top 100 sites) or 'deep' (Top 500 sites)
        """
        self._start()
        
        scan_mode = options.get("scan_mode", "quick")
        
        if not username or len(username) < 3:
            return {"error": "Username too short"}
            
        if not HAS_MAIGRET:
            return {"error": "Maigret library not installed. Please run: pip install maigret"}
        
        console.print(f"[cyan]→ Initializing Maigret Engine ({scan_mode.upper()} Mode)...[/cyan]")
        console.print(f"[dim]  This scans { '100+' if scan_mode == 'quick' else '500+' } sites. Please wait...[/dim]")
        
        results = {
            "target": username,
            "scan_mode": scan_mode,
            "found": [],
            "categories": {},
            "stats": {}
        }
        
        # Run Maigret
        try:
            found_data = asyncio.run(run_maigret(username, scan_mode))
            results["found"] = found_data
            results["count"] = len(found_data)
            
            # Categorize
            for item in found_data:
                cat = item.get("category", "General")
                if cat not in results["categories"]:
                    results["categories"][cat] = []
                results["categories"][cat].append(item)
                
            results["stats"] = {
                "total_found": len(found_data),
                "engine": "Maigret"
            }
            
        except Exception as e:
            console.print(f"[red]Error running Maigret: {e}[/red]")
            results["error"] = str(e)
        
        self._finish()
        results["metadata"] = self.get_metadata()
        
        return results


def scan_username(username: str, scan_mode: str = "quick") -> Dict[str, Any]:
    """Convenience function."""
    return UsernameSearch().scan(username, scan_mode=scan_mode)
