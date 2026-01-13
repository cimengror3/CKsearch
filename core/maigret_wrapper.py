"""
CKSEARCH - Maigret Wrapper (CLI Mode)
=====================================
Wrapper for Maigret CLI tool.
Runs 'maigret' command and parses output.
"""

import asyncio
import shutil
import subprocess
import json
import os
from typing import Dict, Any, List

HAS_MAIGRET = bool(shutil.which("maigret"))

class MaigretWrapper:
    """Wrapper for Maigret CLI."""
    
    def __init__(self):
        self.cmd = shutil.which("maigret")
            
    async def check_username(self, username: str, scan_mode: str = "quick") -> List[Dict]:
        """Run maigret CLI and parse results."""
        if not self.cmd:
            return []
            
        results = []
        
        # Args logic
        # Quick: 50 sites, 10s timeout
        # Deep: 500 sites, 20s timeout
        
        sites_count = "50" if scan_mode == "quick" else "500"
        timeout = "10" if scan_mode == "quick" else "20"
        
        # Command: maigret <username> --top-sites N --timeout T --no-progressbar --no-color --json simple
        args = [
            self.cmd,
            username,
            "--top-sites", sites_count,
            "--timeout", timeout,
            "--no-progressbar",
            "--no-color",
            "--json", "simple",
            "--folderoutput", "/tmp" # Output temp
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Maigret with --json simple creates a file report_<username>.json in folderoutput
            # Check /tmp for the file
            
            report_file = os.path.join("/tmp", f"report_{username}.json")
            
            if os.path.exists(report_file):
                try:
                    with open(report_file, 'r') as f:
                        data = json.load(f)
                        
                    # Parse JSON
                    # Format: { "username": ..., "sites": { "SiteName": { "status": "CLAIMED", "url_user": ... } } }
                    # Or list of results. Maigret json simple format usually:
                    # {"username": ..., "sites": [{"name": "...", "url_user": "...", "status": "CLAIMED"}]}
                    # Let's handle generic format
                    
                    if isinstance(data, dict) and "sites" in data:
                         for site_data in data["sites"]:
                            # If sites is a list of dicts
                             if isinstance(site_data, dict):
                                 status = site_data.get("status", "")
                                 if status and "CLAIMED" in str(status):
                                     results.append({
                                         "site": site_data.get("name"),
                                         "url": site_data.get("url_user"),
                                         "category": self._categorize(site_data.get("name", "")),
                                         "verified": True
                                     })
                             # If sites is a dict (site_name: details)
                             elif isinstance(data["sites"], dict):
                                 for site_name, details in data["sites"].items():
                                     status = details.get("status", "")
                                     if status and "CLAIMED" in str(status):
                                         results.append({
                                             "site": site_name,
                                             "url": details.get("url_user"),
                                             "category": self._categorize(site_name),
                                             "verified": True
                                         })

                    # Cleanup
                    os.remove(report_file)
                    
                except Exception as e:
                    pass
            
            # Fallback output parsing if JSON fail
            if not results:
                # [+] Site: URL
                output = stdout.decode('utf-8', errors='ignore')
                for line in output.splitlines():
                    if "[+]" in line and "http" in line:
                        parts = line.split(":", 1)
                        if len(parts) >= 2:
                            site = parts[0].replace("[+]", "").strip()
                            url = parts[1].strip()
                            results.append({
                                "site": site,
                                "url": url,
                                "category": self._categorize(site),
                                "verified": True
                            })

        except Exception as e:
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
