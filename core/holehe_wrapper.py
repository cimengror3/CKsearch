"""
CKSEARCH - Holehe Wrapper (CLI Mode)
======================================
Wrapper for Holehe CLI tool.
Runs 'holehe' command and parses output.
"""

import asyncio
import shutil
import subprocess
from typing import Dict, Any, List

class HoleheWrapper:
    """Wrapper for Holehe CLI."""
    
    def __init__(self):
        self.cmd = shutil.which("holehe")
            
    async def check_email(self, email: str) -> List[Dict]:
        """Run holehe CLI and parse results."""
        if not self.cmd:
            return []
            
        results = []
        
        # Command: holehe <email> --only-used --no-color --no-clear --no-password-recovery
        # We skip password recovery for speed unless deep scan implied
        
        args = [
            self.cmd,
            email,
            "--only-used",
            "--no-color",
            "--no-clear"
        ]
        
        try:
            # Run asynchronously
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            output = stdout.decode('utf-8', errors='ignore')
            
            # Parse output
            # Holehe output format:
            # [+] twitter
            # [+] instagram
            # [-] facebook
            
            for line in output.splitlines():
                line = line.strip()
                if line.startswith("[+]"):
                    # Example: [+] twitter
                    # Or: [+] twitter (Category) check logic varies
                    
                    parts = line.replace("[+]", "").strip().split()
                    if not parts:
                        continue
                        
                    platform = parts[0]
                    
                    results.append({
                        "platform": platform,
                        "category": self._categorize(platform),
                        "exists": True,
                        "method": "holehe-cli",
                        "details": "Registered"
                    })
                    
        except Exception as e:
            pass
            # print(f"Holehe CLI error: {e}")
            
        return results

    def _categorize(self, name: str) -> str:
        """Categorize platform based on name."""
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
