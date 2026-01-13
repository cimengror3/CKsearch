"""
CKSEARCH - Phone Number Lookup Module (Accurate Edition)
==========================================================
Phone intelligence with clear labeling.
Separates VERIFIED data from manual check links.
"""

import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.table import Table

import config
from core.scanner import BaseScanner
from core.api_client import NumverifyClient

console = Console()


# =============================================================================
# VERIFIED DATA SOURCES (API-based)
# =============================================================================
# These provide REAL verified data via API

# =============================================================================
# MANUAL CHECK LINKS (User must verify themselves)
# =============================================================================

MESSENGER_LINKS = [
    {"name": "WhatsApp", "url": "https://wa.me/{e164_clean}", "note": "Click to check if number has WhatsApp"},
    {"name": "Telegram", "url": "https://t.me/+{e164_clean}", "note": "Open in Telegram to check"},
    {"name": "Viber", "url": "viber://chat?number=+{e164_clean}", "note": "App link - open in Viber"},
    {"name": "Signal", "url": "https://signal.me/#p/+{e164_clean}", "note": "Signal profile link"},
    {"name": "Line", "url": "https://line.me/R/ti/p/+{e164_clean}", "note": "Line app link"},
    {"name": "Zalo", "url": "https://zalo.me/{e164_clean}", "note": "Zalo profile (Vietnam)"},
]

CALLER_ID_SERVICES = [
    {"name": "Truecaller", "url": "https://www.truecaller.com/search/{region}/{local}", "note": "Caller ID lookup"},
    {"name": "Sync.me", "url": "https://sync.me/search/?number=%2B{e164_clean}", "note": "Caller ID database"},
    {"name": "GetContact", "url": "https://getcontact.com/{e164_clean}", "note": "Name lookup"},
    {"name": "Eyecon", "url": "https://www.eyecon.com/", "note": "Caller ID app"},
    {"name": "Hiya", "url": "https://hiya.com/phone/+{e164_clean}", "note": "Spam check"},
]

LOOKUP_SERVICES = [
    {"name": "Whitepages", "url": "https://www.whitepages.com/phone/+{e164_clean}", "note": "US/CA reverse lookup"},
    {"name": "SpyDialer", "url": "https://www.spydialer.com/results.aspx?n={e164_clean}", "note": "Free reverse lookup"},
    {"name": "ThatsThem", "url": "https://thatsthem.com/phone/+{e164_clean}", "note": "People search"},
    {"name": "NumLookup", "url": "https://www.numlookup.com/phone-lookup/{e164_clean}", "note": "Number lookup"},
    {"name": "USPhoneBook", "url": "https://www.usphonebook.com/{e164_clean}", "note": "US phone directory"},
]

SPAM_DATABASES = [
    {"name": "ShouldIAnswer", "url": "https://www.shouldianswer.com/phone-number/+{e164_clean}", "note": "Spam reports"},
    {"name": "Tellows", "url": "https://www.tellows.com/num/+{e164_clean}", "note": "Spam rating"},
    {"name": "CallerComplaints", "url": "https://callercomplaints.com/{e164_clean}", "note": "Complaints"},
    {"name": "800Notes", "url": "https://800notes.com/Phone.aspx/{e164_clean}", "note": "User reports"},
    {"name": "Nomorobo", "url": "https://www.nomorobo.com/lookup/{e164_clean}", "note": "Robocall check"},
]

INDONESIA_SERVICES = [
    {"name": "GetContact ID", "url": "https://getcontact.com/id/+{e164_clean}", "note": "Indonesian caller ID"},
    {"name": "Truecaller ID", "url": "https://www.truecaller.com/search/id/{local}", "note": "Indonesian lookup"},
    {"name": "WhatsApp Business Check", "url": "https://wa.me/{e164_clean}", "note": "Check if business account"},
]

SOCIAL_SEARCH = [
    {"name": "Facebook Search", "url": "https://www.facebook.com/search/top?q={e164}", "note": "Search in Facebook"},
    {"name": "Twitter Search", "url": "https://twitter.com/search?q={e164}", "note": "Search in Twitter"},
    {"name": "Google Search", "url": "https://www.google.com/search?q=\"{e164}\"", "note": "Google exact match"},
    {"name": "LinkedIn Search", "url": "https://www.linkedin.com/search/results/all/?keywords={e164}", "note": "Professional search"},
]

GOOGLE_DORKS = [
    {"name": "Exact Match", "query": '"{e164}"'},
    {"name": "Local Format", "query": '"{local}"'},
    {"name": "With Spaces", "query": '"{formatted}"'},
    {"name": "Contact Pages", "query": '"{e164}" contact OR kontak OR hubungi'},
    {"name": "PDF Files", "query": 'filetype:pdf "{e164}"'},
    {"name": "Data Leaks", "query": '"{e164}" breach OR leak OR dump'},
    {"name": "Pastebin", "query": 'site:pastebin.com "{e164}"'},
]


class PhoneLookup(BaseScanner):
    """Phone Lookup with clear separation of verified vs manual data."""
    
    def __init__(self, language: str = "id"):
        super().__init__("Phone Lookup", language)
        self.numverify = NumverifyClient()
    
    def scan(self, phone_number: str, **options) -> Dict[str, Any]:
        """
        Phone number intelligence scan.
        
        Results are clearly labeled:
        - verified_info: Data from APIs (carrier, location)
        - check_links: Links for manual verification
        """
        self._start()
        
        scan_mode = options.get("scan_mode", "quick")
        
        # 1. Parse & Validate
        console.print("[cyan]→ Parsing phone number...[/cyan]")
        parsed = self._parse_phone(phone_number)
        
        if not parsed.get("valid"):
            self._add_error("Invalid phone number")
            self._finish()
            return {"valid": False, "error": "Invalid phone number format"}
        
        results = {
            "input": phone_number,
            "scan_mode": scan_mode,
            "valid": True,
            
            # VERIFIED DATA (from parsing and APIs)
            "verified_info": {
                "number": parsed["e164"],
                "valid": True,
                "country": parsed.get("region"),
                "country_name": parsed.get("location"),
                "carrier": parsed.get("carrier"),
                "type": parsed.get("type"),
                "timezones": parsed.get("timezones", []),
                "formats": {
                    "e164": parsed["e164"],
                    "national": parsed["national"],
                    "local": parsed["local"],
                },
            },
            
            # API data (if available)
            "api_data": {},
            
            # MANUAL CHECK LINKS (clearly labeled)
            "messenger_links": [],    # WhatsApp, Telegram, etc
            "caller_id_links": [],    # Truecaller, Sync.me, etc
            "lookup_links": [],       # Whitepages, SpyDialer, etc
            "spam_check_links": [],   # Spam databases
            "social_search_links": [],# Social media search
            "indonesia_links": [],    # Indonesia-specific (if ID number)
            "google_dorks": [],       # Google search queries
        }
        
        e164_clean = parsed["e164"].replace("+", "")
        local = parsed["local"]
        region = parsed["region"]
        formatted = parsed["national"]
        
        # 2. Numverify API (real data)
        console.print("[cyan]→ Querying carrier API...[/cyan]")
        nv_data = self.numverify.validate(parsed["e164"])
        if nv_data:
            results["api_data"] = {
                "carrier": nv_data.get("carrier"),
                "line_type": nv_data.get("line_type"),
                "location": nv_data.get("location"),
                "country": nv_data.get("country_name"),
                "source": "Numverify API",
            }
            # Update verified info with API data
            if nv_data.get("carrier"):
                results["verified_info"]["carrier"] = nv_data.get("carrier")
            if nv_data.get("line_type"):
                results["verified_info"]["type"] = nv_data.get("line_type")
        
        # 3. Generate all check links
        console.print("[cyan]→ Generating verification links...[/cyan]")
        
        # Messenger
        results["messenger_links"] = self._generate_links(
            MESSENGER_LINKS, e164_clean=e164_clean, e164=parsed["e164"]
        )
        
        # Caller ID
        results["caller_id_links"] = self._generate_links(
            CALLER_ID_SERVICES, e164_clean=e164_clean, region=region.lower(), local=local
        )
        
        # Lookup (deep only)
        if scan_mode == "deep":
            results["lookup_links"] = self._generate_links(
                LOOKUP_SERVICES, e164_clean=e164_clean
            )
            
            results["spam_check_links"] = self._generate_links(
                SPAM_DATABASES, e164_clean=e164_clean
            )
        
        # Social search
        results["social_search_links"] = self._generate_links(
            SOCIAL_SEARCH, e164=parsed["e164"], e164_clean=e164_clean
        )
        
        # Indonesia specific
        if region == "ID":
            results["indonesia_links"] = self._generate_links(
                INDONESIA_SERVICES, e164_clean=e164_clean, local=local
            )
        
        # Google dorks
        results["google_dorks"] = self._generate_dorks(
            GOOGLE_DORKS, e164=parsed["e164"], local=local, formatted=formatted
        )
        
        # Summary
        total_links = sum([
            len(results["messenger_links"]),
            len(results["caller_id_links"]),
            len(results["lookup_links"]),
            len(results["spam_check_links"]),
            len(results["social_search_links"]),
            len(results["indonesia_links"]),
            len(results["google_dorks"]),
        ])
        results["stats"] = {
            "total_check_links": total_links,
            "has_api_data": bool(results["api_data"]),
        }
        
        self._finish()
        results["metadata"] = self.get_metadata()
        
        # Display summary
        self._display_summary(results)
        
        return results
    
    def _parse_phone(self, phone: str) -> Dict[str, Any]:
        """Parse and validate phone number."""
        try:
            parsed = phonenumbers.parse(phone, None)
            if not phonenumbers.is_valid_number(parsed):
                return {"valid": False}
            
            e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            national = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
            region = phonenumbers.region_code_for_number(parsed)
            
            # Local format
            local = national.replace(" ", "").replace("-", "")
            if region == "ID" and not local.startswith("0"):
                local = "0" + str(parsed.national_number)
            
            return {
                "valid": True,
                "e164": e164,
                "national": national,
                "local": local,
                "region": region,
                "carrier": carrier.name_for_number(parsed, "en"),
                "location": geocoder.description_for_number(parsed, "en"),
                "timezones": list(timezone.time_zones_for_number(parsed)),
                "type": self._get_type(parsed),
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def _get_type(self, parsed) -> str:
        t = phonenumbers.number_type(parsed)
        types = {
            phonenumbers.PhoneNumberType.MOBILE: "Mobile",
            phonenumbers.PhoneNumberType.FIXED_LINE: "Landline",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Mobile/Landline",
            phonenumbers.PhoneNumberType.TOLL_FREE: "Toll Free",
            phonenumbers.PhoneNumberType.PREMIUM_RATE: "Premium Rate",
            phonenumbers.PhoneNumberType.VOIP: "VoIP",
        }
        return types.get(t, "Unknown")
    
    def _generate_links(self, template_list: List[Dict], **kwargs) -> List[Dict]:
        """Generate links from template."""
        links = []
        for item in template_list:
            url = item["url"]
            for key, val in kwargs.items():
                url = url.replace("{" + key + "}", str(val))
            
            links.append({
                "name": item["name"],
                "url": url,
                "note": item.get("note", ""),
            })
        return links
    
    def _generate_dorks(self, template_list: List[Dict], **kwargs) -> List[Dict]:
        """Generate Google dork queries."""
        dorks = []
        for item in template_list:
            query = item["query"]
            for key, val in kwargs.items():
                query = query.replace("{" + key + "}", str(val))
            
            url = f"https://www.google.com/search?q={query.replace(' ', '+').replace('\"', '%22')}"
            dorks.append({
                "name": item["name"],
                "query": query,
                "url": url,
            })
        return dorks
    
    def _display_summary(self, results: Dict):
        """Display a summary of verified info."""
        console.print()
        
        table = Table(title="📱 Verified Phone Info", show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        vi = results["verified_info"]
        table.add_row("Number", vi["number"])
        table.add_row("Country", f"{vi.get('country', 'N/A')} - {vi.get('country_name', 'N/A')}")
        table.add_row("Carrier", vi.get("carrier") or "Unknown")
        table.add_row("Type", vi.get("type") or "Unknown")
        
        if results["api_data"]:
            api = results["api_data"]
            if api.get("line_type"):
                table.add_row("Line Type", api["line_type"])
        
        console.print(table)
        
        console.print(f"\n[dim]Generated {results['stats']['total_check_links']} verification links.[/dim]")
        console.print("[dim]Note: Links are for manual verification - results not guaranteed.[/dim]")


def scan_phone(phone: str, scan_mode: str = "quick") -> Dict[str, Any]:
    return PhoneLookup().scan(phone, scan_mode=scan_mode)
