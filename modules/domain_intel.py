"""
CKSEARCH - Domain Intelligence Module (Enhanced)
=================================================
Domain analysis and reconnaissance with VirusTotal integration.
"""

import socket
import ssl
import re
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional, List
from rich.console import Console

import config
from core.scanner import BaseScanner
from core.api_client import APIClient

console = Console()


class DomainIntel(BaseScanner):
    """Enhanced Domain intelligence scanner with VirusTotal."""
    
    def __init__(self, language: str = "id"):
        super().__init__("Domain Intelligence", language)
        self.http_client = APIClient()
        self.virustotal_key = config.API_KEYS.get("virustotal")
    
    def scan(self, domain: str, **options) -> Dict[str, Any]:
        """
        Perform comprehensive domain analysis.
        
        Args:
            domain: Domain to analyze
            scan_mode: 'quick' or 'deep'
        """
        self._start()
        
        scan_mode = options.get("scan_mode", "quick")
        
        # Clean domain
        domain = self._clean_domain(domain)
        
        if not self._validate_domain(domain):
            self._add_error("Invalid domain format")
            self._finish()
            return {"error": "Invalid domain format"}
        
        results = {
            "domain": domain,
            "scan_mode": scan_mode,
            "whois": {},
            "dns_records": {},
            "ssl_certificate": {},
            "ip_addresses": [],
            "nameservers": [],
            "mx_records": [],
            "subdomains": [],
            "technology_stack": {},
            "security_headers": {},
            "web_info": {},
            "reputation": {},
        }
        
        # 1. WHOIS lookup
        console.print("[cyan]→ Fetching WHOIS information...[/cyan]")
        whois_data = self._get_whois(domain)
        results["whois"] = whois_data
        
        # 2. DNS Records
        console.print("[cyan]→ Querying DNS records...[/cyan]")
        dns_data = self._get_dns_records(domain)
        results["dns_records"] = dns_data
        results["ip_addresses"] = dns_data.get("A", [])
        results["nameservers"] = dns_data.get("NS", [])
        results["mx_records"] = dns_data.get("MX", [])
        
        # 3. SSL Certificate
        console.print("[cyan]→ Analyzing SSL certificate...[/cyan]")
        ssl_data = self._get_ssl_info(domain)
        results["ssl_certificate"] = ssl_data
        
        # 4. Technology detection
        console.print("[cyan]→ Detecting technologies...[/cyan]")
        tech_data = self._detect_technologies(domain)
        results["technology_stack"] = tech_data
        
        # 5. Security headers
        console.print("[cyan]→ Checking security headers...[/cyan]")
        headers_data = self._check_security_headers(domain)
        results["security_headers"] = headers_data
        
        # 6. Web information
        console.print("[cyan]→ Gathering web information...[/cyan]")
        web_info = self._get_web_info(domain)
        results["web_info"] = web_info
        
        # 7. Subdomain enumeration (Enhanced)
        if scan_mode == "deep":
            console.print("[cyan]→ Enumerating subdomains (Deep)...[/cyan]")
            subdomains = self._enumerate_subdomains(domain, deep=True)
        else:
            console.print("[cyan]→ Enumerating subdomains (Quick)...[/cyan]")
            subdomains = self._enumerate_subdomains(domain, deep=False)
        results["subdomains"] = subdomains
        
        # 8. VirusTotal Analysis
        if self.virustotal_key:
            console.print("[cyan]→ Checking VirusTotal reputation...[/cyan]")
            vt_data = self._check_virustotal(domain)
            results["reputation"]["virustotal"] = vt_data
        else:
            results["reputation"]["virustotal"] = {"error": "No API key provided"}
        
        # 9. Calculate security score
        results["security_assessment"] = self._assess_security(results)
        
        self._finish()
        results["metadata"] = self.get_metadata()
        
        return results
    
    def _clean_domain(self, domain: str) -> str:
        """Clean and normalize domain."""
        domain = domain.lower().strip()
        domain = re.sub(r'^https?://', '', domain)
        domain = domain.split('/')[0]
        domain = re.sub(r'^www\.', '', domain)
        return domain
    
    def _validate_domain(self, domain: str) -> bool:
        """Validate domain format."""
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$'
        return bool(re.match(pattern, domain))
    
    def _get_whois(self, domain: str) -> Dict[str, Any]:
        """Get WHOIS information."""
        try:
            import whois
            w = whois.whois(domain)
            
            def safe_get(v):
                return v[0] if isinstance(v, list) and v else v
            
            def date_str(d):
                if isinstance(d, list): d = d[0] if d else None
                return d.isoformat() if isinstance(d, datetime) else str(d) if d else None
            
            return {
                "registrar": safe_get(w.registrar),
                "creation_date": date_str(w.creation_date),
                "expiration_date": date_str(w.expiration_date),
                "name_servers": w.name_servers or [],
                "organization": safe_get(w.org),
                "country": safe_get(w.country),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_dns_records(self, domain: str) -> Dict[str, List]:
        """Get DNS records."""
        import dns.resolver
        records = {}
        resolver = dns.resolver.Resolver()
        resolver.timeout = 2
        resolver.lifetime = 2
        
        for rtype in ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA']:
            try:
                answers = resolver.resolve(domain, rtype)
                if rtype == 'MX':
                    records[rtype] = [{"priority": a.preference, "host": str(a.exchange).rstrip('.')} for a in answers]
                elif rtype == 'SOA':
                    for a in answers:
                         records[rtype] = {
                            "mname": str(a.mname).rstrip('.'),
                            "rname": str(a.rname).rstrip('.'),
                            "serial": a.serial
                        }
                else:
                    records[rtype] = [str(a).rstrip('.').strip('"') for a in answers]
            except: pass
        return records
    
    def _get_ssl_info(self, domain: str) -> Dict[str, Any]:
        """Get SSL certificate information."""
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    subj = dict(x[0] for x in cert.get('subject', []))
                    iss = dict(x[0] for x in cert.get('issuer', []))
                    not_after = cert.get('notAfter')
                    days = None
                    if not_after:
                        exp = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                        days = (exp - datetime.now()).days
                    return {
                        "valid": True, "subject": subj.get('commonName'),
                        "issuer": iss.get('commonName'), "expires": not_after,
                        "days_until_expiry": days,
                        "organization": subj.get('organizationName'),
                    }
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def _detect_technologies(self, domain: str) -> Dict[str, Any]:
        """Detect web technologies used."""
        tech = {"cms": None, "server": None, "cdn": None, "frameworks": []}
        try:
            resp = self.http_client.session.get(f"https://{domain}", timeout=10)
            h = resp.headers
            html = resp.text.lower()
            
            tech["server"] = h.get('Server')
            
            # CDN Detection
            if 'cf-ray' in h: tech["cdn"] = "Cloudflare"
            elif 'x-cdn' in h: tech["cdn"] = "Generic CDN"
            elif 'x-amz-cf-id' in h: tech["cdn"] = "Amazon CloudFront"
            
            # CMS Detection
            if 'wp-content' in html: tech["cms"] = "WordPress"
            elif 'drupal' in html: tech["cms"] = "Drupal"
            elif 'shopify' in html: tech["cms"] = "Shopify"
            elif 'wix.com' in html: tech["cms"] = "Wix"
            
            # Framework Detection
            frameworks = [
                ('react', 'React'), ('vue', 'Vue.js'), ('angular', 'Angular'),
                ('jquery', 'jQuery'), ('bootstrap', 'Bootstrap'),
                ('laravel', 'Laravel'), ('django', 'Django')
            ]
            for key, name in frameworks:
                if key in html: tech["frameworks"].append(name)
                
        except: pass
        return tech
    
    def _check_security_headers(self, domain: str) -> Dict[str, Any]:
        """Check security headers."""
        result = {"present": [], "missing": [], "grade": "F"}
        headers_check = [
            'Strict-Transport-Security', 'Content-Security-Policy',
            'X-Frame-Options', 'X-Content-Type-Options', 'X-XSS-Protection'
        ]
        try:
            resp = self.http_client.session.get(f"https://{domain}", timeout=10)
            for h in headers_check:
                if h in resp.headers: result["present"].append(h)
                else: result["missing"].append(h)
            
            # Simplified grading
            pct = len(result["present"]) / len(headers_check) * 100
            result["grade"] = "A" if pct >= 80 else "B" if pct >= 60 else "C" if pct >= 40 else "D" if pct >= 20 else "F"
        except: pass
        return result
    
    def _get_web_info(self, domain: str) -> Dict[str, Any]:
        """Get web info (title, description)."""
        info = {"title": None, "description": None, "https": False}
        try:
            resp = self.http_client.session.get(f"https://{domain}", timeout=10)
            info["https"] = True
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            if soup.title:
                info["title"] = soup.title.string.strip()
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                info["description"] = meta_desc.get('content', '').strip()
        except: pass
        return info

    def _enumerate_subdomains(self, domain: str, deep: bool = False) -> List[Dict]:
        """Enumerate subdomains using DNS and Wordlist."""
        import dns.resolver
        found = []
        resolver = dns.resolver.Resolver()
        resolver.timeout = 1
        resolver.lifetime = 1

        # Check CRT.SH first (Passive)
        try:
             url = f"https://crt.sh/?q=%.{domain}&output=json"
             resp = self.http_client.session.get(url, timeout=10)
             if resp.status_code == 200:
                 data = resp.json()
                 crt_subs = set()
                 for entry in data:
                     name = entry['name_value']
                     if '\n' in name: # Handle multi-value
                         for n in name.split('\n'):
                             crt_subs.add(n)
                     else:
                         crt_subs.add(name)
                 
                 for sub in crt_subs:
                     # Simple wildcards removal
                     if '*' not in sub:
                         found.append({"subdomain": sub, "source": "crt.sh"})
        except Exception as e:
            pass # Fail silently for passive check

        # Active Brute-force
        # Basic list for Quick Mode
        wordlist = ['www', 'mail', 'remote', 'blog', 'webmail', 'server', 'ns1', 'ns2', 'smtp', 'secure', 'vpn', 'm', 'shop', 'admin', 'test', 'dev', 'api']
        
        # Extended list for Deep Mode
        if deep:
            wordlist.extend([
                'portal', 'mobile', 'support', 'dev', 'beta', 'auth', 'staging', 'dashboard', 'cpanel',
                'docs', 'status', 'account', 'login', 'corp', 'internal', 'demo', 'download', 'cdn',
                'app', 'db', 'sql', 'mysql', 'oracle', 'jira', 'git', 'gitlab', 'jenkins', 'marketing'
            ])

        for sub in wordlist:
            full_sub = f"{sub}.{domain}"
            # Check if we already found it via passive scan
            if any(f['subdomain'] == full_sub for f in found):
                 continue

            try:
                ans = resolver.resolve(full_sub, 'A')
                found.append({"subdomain": full_sub, "ips": [str(a) for a in ans], "source": "dns_brute"})
            except: pass
            
        return found

    def _check_virustotal(self, domain: str) -> Dict[str, Any]:
        """Check domain reputation using VirusTotal API."""
        if not self.virustotal_key:
            return {"error": "No API key"}
            
        url = f"https://www.virustotal.com/api/v3/domains/{domain}"
        headers = {
            "x-apikey": self.virustotal_key
        }
        
        try:
            resp = self.http_client.session.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("data", {}).get("attributes", {})
                stats = data.get("last_analysis_stats", {})
                
                return {
                    "harmless": stats.get("harmless", 0),
                    "malicious": stats.get("malicious", 0),
                    "suspicious": stats.get("suspicious", 0),
                    "reputation": data.get("reputation", 0),
                    "categories": data.get("categories", {}),
                    "link": f"https://www.virustotal.com/gui/domain/{domain}"
                }
            elif resp.status_code == 401:
                 return {"error": "Invalid API Key"}
            elif resp.status_code == 404:
                 return {"error": "Domain not found in VirusTotal"}
            else:
                 return {"error": f"API Error {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def _assess_security(self, results: Dict) -> Dict[str, Any]:
        """Assess security score."""
        score = 100
        issues = []
        
        # SSL
        if not results.get("ssl_certificate", {}).get("valid"):
            score -= 30; issues.append("Invalid SSL")
        
        # Headers
        missing_h = len(results.get("security_headers", {}).get("missing", []))
        score -= missing_h * 5
        if missing_h: issues.append(f"Missing {missing_h} security headers")
        
        # VirusTotal
        vt_malicious = results.get("reputation", {}).get("virustotal", {}).get("malicious", 0)
        if isinstance(vt_malicious, int) and vt_malicious > 0:
            score -= 50
            issues.append(f"Flagged malicious by {vt_malicious} vendors")

        grade = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D" if score >= 40 else "F"
        return {"score": max(0, score), "grade": grade, "issues": issues}


def analyze_domain(domain: str, scan_mode: str = "quick") -> Dict[str, Any]:
    return DomainIntel().scan(domain, scan_mode=scan_mode)
