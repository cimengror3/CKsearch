"""
CKSEARCH - IP Scanner Module
=============================
IP/Server intelligence with passive and active scanning.
"""

import socket
import asyncio
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

import config
from core.scanner import BaseScanner, PortScanner
from core.api_client import IPInfoClient, APIClient

console = Console()


class IPScanner(BaseScanner):
    """IP/Server scanner with passive and active modes."""
    
    def __init__(self, language: str = "id"):
        super().__init__("IP Scanner", language)
        self.ipinfo = IPInfoClient()
        self.http_client = APIClient()
        self.port_scanner = PortScanner(timeout=2.0)
    
    def scan(self, ip_address: str, **options) -> Dict[str, Any]:
        """
        Scan IP address for information.
        
        Args:
            ip_address: IP address or hostname
            scan_type: 'passive', 'active', or 'both'
        """
        self._start()
        
        scan_type = options.get("scan_type", "both")
        
        # Resolve hostname to IP if needed
        resolved_ip = self._resolve_host(ip_address)
        if not resolved_ip:
            self._add_error("Could not resolve host")
            self._finish()
            return {"error": "Could not resolve host"}
        
        results = {
            "target": ip_address,
            "ip": resolved_ip,
            "passive_scan": {},
            "active_scan": {},
        }
        
        # Passive scan
        if scan_type in ["passive", "both"]:
            console.print("[cyan]→ Running passive scan...[/cyan]")
            results["passive_scan"] = self._passive_scan(resolved_ip)
        
        # Active scan
        if scan_type in ["active", "both"]:
            console.print("[cyan]→ Running active scan...[/cyan]")
            results["active_scan"] = asyncio.run(self._active_scan(resolved_ip))
        
        # Combine and analyze
        results["analysis"] = self._analyze_results(results)
        
        self._finish()
        results["metadata"] = self.get_metadata()
        return results
    
    def _resolve_host(self, host: str) -> Optional[str]:
        """Resolve hostname to IP address."""
        try:
            # Check if already IP
            socket.inet_aton(host)
            return host
        except socket.error:
            pass
        
        try:
            return socket.gethostbyname(host)
        except socket.gaierror:
            return None
    
    def _passive_scan(self, ip: str) -> Dict[str, Any]:
        """Perform passive reconnaissance."""
        results = {
            "geolocation": {},
            "asn": {},
            "reverse_dns": None,
            "abuse_contact": None,
            "privacy": {},
        }
        
        # IPInfo lookup
        console.print("  [dim]• Querying IPInfo...[/dim]")
        ipinfo_data = self.ipinfo.lookup(ip)
        if ipinfo_data:
            results["geolocation"] = {
                "city": ipinfo_data.get("city"),
                "region": ipinfo_data.get("region"),
                "country": ipinfo_data.get("country"),
                "country_name": self._country_name(ipinfo_data.get("country")),
                "postal": ipinfo_data.get("postal"),
                "timezone": ipinfo_data.get("timezone"),
                "loc": ipinfo_data.get("loc"),
            }
            results["asn"] = {
                "org": ipinfo_data.get("org"),
                "hostname": ipinfo_data.get("hostname"),
            }
        
        # Reverse DNS
        console.print("  [dim]• Checking reverse DNS...[/dim]")
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            results["reverse_dns"] = hostname
        except socket.herror:
            results["reverse_dns"] = None
        
        # Additional checks
        results["shodan_url"] = f"https://www.shodan.io/host/{ip}"
        results["censys_url"] = f"https://search.censys.io/hosts/{ip}"
        results["virustotal_url"] = f"https://www.virustotal.com/gui/ip-address/{ip}"
        
        return results
    
    async def _active_scan(self, ip: str) -> Dict[str, Any]:
        """Perform active port scanning."""
        results = {
            "open_ports": [],
            "services": [],
            "os_hints": [],
        }
        
        # Port scan
        console.print("  [dim]• Scanning common ports...[/dim]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Port scanning...", total=len(config.COMMON_PORTS))
            
            # Scan ports
            open_ports = await self.port_scanner.scan_ports(ip, config.COMMON_PORTS)
            progress.update(task, completed=len(config.COMMON_PORTS))
        
        results["open_ports"] = open_ports
        
        # Analyze services
        for port_info in open_ports:
            if port_info["state"] == "open":
                service = {
                    "port": port_info["port"],
                    "service": port_info["service"],
                    "banner": port_info.get("banner"),
                }
                results["services"].append(service)
                
                # OS hints from banners
                banner = port_info.get("banner", "").lower()
                if "ubuntu" in banner: results["os_hints"].append("Ubuntu Linux")
                elif "debian" in banner: results["os_hints"].append("Debian Linux")
                elif "centos" in banner: results["os_hints"].append("CentOS")
                elif "windows" in banner: results["os_hints"].append("Windows")
                elif "openssh" in banner: results["os_hints"].append("Linux/Unix (OpenSSH)")
        
        results["os_hints"] = list(set(results["os_hints"]))
        
        return results
    
    def _analyze_results(self, results: Dict) -> Dict[str, Any]:
        """Analyze scan results for security insights."""
        analysis = {
            "risk_level": "low",
            "findings": [],
            "recommendations": [],
        }
        
        passive = results.get("passive_scan", {})
        active = results.get("active_scan", {})
        
        # Check for risky open ports
        risky_ports = {
            21: "FTP (unencrypted)",
            23: "Telnet (unencrypted)",
            3389: "RDP (exposed)",
            445: "SMB (exposed)",
            3306: "MySQL (exposed)",
            27017: "MongoDB (exposed)",
            6379: "Redis (exposed)",
        }
        
        open_ports = active.get("open_ports", [])
        for port_info in open_ports:
            if port_info["state"] == "open" and port_info["port"] in risky_ports:
                analysis["findings"].append(f"Risky port open: {port_info['port']} ({risky_ports[port_info['port']]})")
                analysis["risk_level"] = "high"
        
        # Recommendations
        if analysis["risk_level"] == "high":
            analysis["recommendations"].extend([
                "Review exposed services and restrict access",
                "Use firewall to limit port access",
                "Consider VPN for sensitive services",
            ])
        
        open_count = len([p for p in open_ports if p["state"] == "open"])
        analysis["summary"] = f"{open_count} open ports detected"
        
        return analysis
    
    def _country_name(self, code: str) -> str:
        """Get country name from code."""
        countries = {
            "US": "United States", "ID": "Indonesia", "SG": "Singapore",
            "JP": "Japan", "CN": "China", "KR": "South Korea",
            "DE": "Germany", "GB": "United Kingdom", "NL": "Netherlands",
            "FR": "France", "AU": "Australia", "IN": "India",
        }
        return countries.get(code, code)


def scan_ip(ip: str, scan_type: str = "both") -> Dict[str, Any]:
    """Quick IP scan function."""
    return IPScanner().scan(ip, scan_type=scan_type)
