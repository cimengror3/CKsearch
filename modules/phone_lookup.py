"""
CKSEARCH - Phone Number Lookup Module (Ultimate Edition)
==========================================================
Comprehensive phone number intelligence with 50+ check sources.
"""

import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from typing import Dict, Any, Optional, List
from rich.console import Console
import time

import config
from core.scanner import BaseScanner
from core.api_client import NumverifyClient

console = Console()


# =============================================================================
# PHONE CHECK PLATFORMS DATABASE
# =============================================================================

# Messenger & Social Apps (Check by phone number)
MESSENGER_PLATFORMS = [
    # Global Messengers
    {"name": "WhatsApp", "url": "https://wa.me/{phone}", "type": "Direct", "category": "Messenger"},
    {"name": "Telegram", "url": "https://t.me/+{phone}", "type": "Profile", "category": "Messenger"},
    {"name": "Viber", "url": "viber://chat?number={phone}", "type": "App", "category": "Messenger"},
    {"name": "Signal", "url": "https://signal.me/#p/{e164}", "type": "Profile", "category": "Messenger"},
    {"name": "IMO", "url": "https://imo.im/app?to={phone}", "type": "App", "category": "Messenger"},
    
    # Asian Messengers
    {"name": "Line", "url": "https://line.me/R/ti/p/{phone}", "type": "App", "category": "Asia"},
    {"name": "KakaoTalk", "url": "https://open.kakao.com/phonenumber/{phone}", "type": "App", "category": "Asia"},
    {"name": "WeChat", "url": "weixin://dl/business/?t={phone}", "type": "App", "category": "Asia"},
    {"name": "Zalo", "url": "https://zalo.me/{phone}", "type": "App", "category": "Asia"},
    
    # Video Call
    {"name": "Skype", "url": "skype:{phone}?call", "type": "App", "category": "Video"},
    {"name": "Zoom", "url": "https://zoom.us/j/{phone}", "type": "General", "category": "Video"},
    {"name": "Google Meet", "url": "https://meet.google.com/{phone}", "type": "General", "category": "Video"},
]

# Phone Lookup Services (Caller ID / Spam Check)
PHONE_LOOKUP_SERVICES = [
    # Global Caller ID
    {"name": "Truecaller", "url": "https://www.truecaller.com/search/{region}/{phone_local}", "type": "CallerID", "category": "Lookup"},
    {"name": "Sync.me", "url": "https://sync.me/search/?number=%2B{phone}", "type": "CallerID", "category": "Lookup"},
    {"name": "CallerID Test", "url": "https://calleridtest.com/look-up/{phone}", "type": "CallerID", "category": "Lookup"},
    {"name": "WhoCalled.us", "url": "https://whocalled.us/lookup/{phone}", "type": "Spam", "category": "Lookup"},
    {"name": "NumLookup", "url": "https://www.numlookup.com/phone-lookup/{phone}", "type": "CallerID", "category": "Lookup"},
    {"name": "SpyDialer", "url": "https://www.spydialer.com/results.aspx?n={phone}", "type": "Reverse", "category": "Lookup"},
    {"name": "ThatsThem", "url": "https://thatsthem.com/phone/{phone}", "type": "Reverse", "category": "Lookup"},
    {"name": "USPhoneBook", "url": "https://www.usphonebook.com/{phone}", "type": "Reverse", "category": "Lookup"},
    {"name": "NumberGuru", "url": "https://www.numberguru.com/phone/{phone}", "type": "Reverse", "category": "Lookup"},
    {"name": "WhoCallsMe", "url": "https://whocallsme.com/Phone-Number.aspx/{phone}", "type": "Spam", "category": "Lookup"},
    
    # Spam Databases
    {"name": "ShouldIAnswer", "url": "https://www.shouldianswer.com/phone-number/{phone}", "type": "Spam", "category": "Spam"},
    {"name": "Tellows", "url": "https://www.tellows.com/num/{phone}", "type": "Spam", "category": "Spam"},
    {"name": "CallerComplaints", "url": "https://callercomplaints.com/{phone}", "type": "Spam", "category": "Spam"},
    {"name": "800Notes", "url": "https://800notes.com/Phone.aspx/{phone}", "type": "Spam", "category": "Spam"},
    {"name": "Nomorobo", "url": "https://www.nomorobo.com/lookup/{phone}", "type": "Spam", "category": "Spam"},
    
    # International
    {"name": "GetContact", "url": "https://getcontact.com/{phone}", "type": "CallerID", "category": "International"},
    {"name": "Hiya", "url": "https://hiya.com/phone/{phone}", "type": "CallerID", "category": "International"},
    {"name": "CallerSmart", "url": "https://callersmart.com/phone-number/{phone}", "type": "CallerID", "category": "International"},
    {"name": "Whitepages", "url": "https://www.whitepages.com/phone/{phone}", "type": "Reverse", "category": "Lookup"},
    {"name": "BeenVerified", "url": "https://www.beenverified.com/phone/{phone}", "type": "Reverse", "category": "Lookup"},
    {"name": "Intelius", "url": "https://www.intelius.com/phone/{phone}", "type": "Reverse", "category": "Lookup"},
    {"name": "Spokeo", "url": "https://www.spokeo.com/{phone}", "type": "Reverse", "category": "Lookup"},
    {"name": "PeopleFinder", "url": "https://www.peoplefinder.com/phone/{phone}", "type": "Reverse", "category": "Lookup"},
]

# Indonesia-specific
INDONESIA_PHONE_SERVICES = [
    {"name": "GetContact ID", "url": "https://getcontact.com/id/{phone}", "type": "CallerID", "category": "Indonesia"},
    {"name": "Truecaller ID", "url": "https://www.truecaller.com/search/id/{phone_local}", "type": "CallerID", "category": "Indonesia"},
    {"name": "WA Business Check", "url": "https://wa.me/{phone}?text=test", "type": "Business", "category": "Indonesia"},
    {"name": "GoPay/Gojek", "url": "https://gojek.com/phone/{phone}", "type": "eWallet", "category": "Indonesia"},
    {"name": "OVO", "url": "https://ovo.id/send/{phone}", "type": "eWallet", "category": "Indonesia"},
    {"name": "DANA", "url": "https://dana.id/qr/{phone}", "type": "eWallet", "category": "Indonesia"},
    {"name": "ShopeePay", "url": "https://shopee.co.id/user/{phone}", "type": "eWallet", "category": "Indonesia"},
    {"name": "LinkAja", "url": "https://www.linkaja.id/send/{phone}", "type": "eWallet", "category": "Indonesia"},
    {"name": "Tokopedia", "url": "https://www.tokopedia.com/search?q={phone}", "type": "Search", "category": "Indonesia"},
    {"name": "Bukalapak", "url": "https://www.bukalapak.com/products?search[keywords]={phone}", "type": "Search", "category": "Indonesia"},
]

# Social Media Search by Phone
SOCIAL_PHONE_SEARCH = [
    {"name": "Facebook", "url": "https://www.facebook.com/search/top?q={phone}", "type": "Search", "category": "Social"},
    {"name": "Twitter/X", "url": "https://twitter.com/search?q={phone}", "type": "Search", "category": "Social"},
    {"name": "Instagram", "url": "https://www.instagram.com/explore/tags/{phone_local}/", "type": "Search", "category": "Social"},
    {"name": "LinkedIn", "url": "https://www.linkedin.com/search/results/all/?keywords={phone}", "type": "Search", "category": "Social"},
    {"name": "TikTok", "url": "https://www.tiktok.com/search?q={phone}", "type": "Search", "category": "Social"},
    {"name": "VK", "url": "https://vk.com/search?c[q]={phone}&c[section]=auto", "type": "Search", "category": "Social"},
]

# Google Dork Queries
GOOGLE_DORKS_PHONE = [
    {"name": "Exact Match", "query": '"{phone}"', "category": "Google"},
    {"name": "Local Format", "query": '"{phone_local}"', "category": "Google"},
    {"name": "With Spaces", "query": '"{phone_spaced}"', "category": "Google"},
    {"name": "Site Facebook", "query": 'site:facebook.com "{phone}"', "category": "Google"},
    {"name": "Site Instagram", "query": 'site:instagram.com "{phone}"', "category": "Google"},
    {"name": "Site LinkedIn", "query": 'site:linkedin.com "{phone}"', "category": "Google"},
    {"name": "Contact Page", "query": '"{phone}" contact OR kontak OR hubungi', "category": "Google"},
    {"name": "PDF/Doc Files", "query": 'filetype:pdf OR filetype:doc "{phone}"', "category": "Google"},
    {"name": "Pastebin", "query": 'site:pastebin.com "{phone}"', "category": "Google"},
    {"name": "Data Breach", "query": '"{phone}" breach OR leak OR dump', "category": "Google"},
]


class PhoneLookup(BaseScanner):
    """Ultimate Phone Number Scanner with 50+ sources."""
    
    def __init__(self, language: str = "id"):
        super().__init__("Phone Lookup", language)
        self.numverify = NumverifyClient()
    
    def scan(self, phone_number: str, **options) -> Dict[str, Any]:
        """
        Comprehensive phone number scan.
        
        Args:
           phone_number: Number to scan (e.g., +62812345678)
           scan_mode: 'quick' or 'deep'
        """
        self._start()
        
        scan_mode = options.get("scan_mode", "quick")
        
        # 1. Parse & Validate
        console.print("[cyan]→ Validating phone number...[/cyan]")
        basic_info = self._parse_phone(phone_number)
        
        if not basic_info.get("valid"):
            self._add_error("Invalid phone number")
            self._finish()
            return {"valid": False, "error": "Invalid phone number format"}
        
        phone = basic_info["e164"]
        phone_clean = basic_info["clean"]
        phone_local = basic_info["local"]
        region = basic_info["region"]
        
        results = {
            "input": phone_number,
            "scan_mode": scan_mode,
            "valid": True,
            "parsed": basic_info,
            "carrier_info": {},
            "messenger_checks": [],
            "lookup_services": [],
            "social_search": [],
            "indonesia_services": [],
            "google_dorks": [],
            "hlr_info": {},
        }
        
        # 2. Numverify API
        console.print("[cyan]→ Querying Numverify API...[/cyan]")
        nv_data = self.numverify.validate(phone)
        if nv_data:
            results["carrier_info"] = {
                "carrier": nv_data.get("carrier"),
                "location": nv_data.get("location"),
                "line_type": nv_data.get("line_type"),
                "country": nv_data.get("country_name"),
            }
        
        # 3. Generate Messenger Links
        console.print("[cyan]→ Generating messenger check links...[/cyan]")
        results["messenger_checks"] = self._generate_messenger_links(phone_clean, phone)
        
        # 4. Generate Lookup Service Links
        console.print("[cyan]→ Generating lookup service links...[/cyan]")
        results["lookup_services"] = self._generate_lookup_links(phone_clean, phone_local, region)
        
        # 5. Social Media Search
        console.print("[cyan]→ Generating social media search links...[/cyan]")
        results["social_search"] = self._generate_social_links(phone, phone_local)
        
        # 6. Indonesia-specific (if Indonesian number)
        if region == "ID":
            console.print("[cyan]→ Generating Indonesia-specific services...[/cyan]")
            results["indonesia_services"] = self._generate_indonesia_links(phone_clean, phone_local)
        
        # 7. Google Dorks
        console.print("[cyan]→ Generating Google dork queries...[/cyan]")
        results["google_dorks"] = self._generate_google_dorks(phone, phone_local)
        
        # 8. HLR Simulation (Deep only)
        if scan_mode == "deep":
            console.print("[cyan]→ Performing HLR analysis...[/cyan]")
            results["hlr_info"] = self._simulate_hlr(basic_info)
        
        # Summary
        total_checks = (
            len(results["messenger_checks"]) +
            len(results["lookup_services"]) +
            len(results["social_search"]) +
            len(results["indonesia_services"]) +
            len(results["google_dorks"])
        )
        results["total_check_links"] = total_checks
        
        self._finish()
        results["metadata"] = self.get_metadata()
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
            
            # Clean formats
            clean = e164.replace("+", "")
            local = national.replace(" ", "").replace("-", "")
            if region == "ID" and not local.startswith("0"):
                local = "0" + str(parsed.national_number)
            
            # Spaced format for search
            spaced = " ".join([e164[i:i+4] for i in range(0, len(e164), 4)])
            
            return {
                "valid": True,
                "e164": e164,
                "national": national,
                "clean": clean,
                "local": local,
                "spaced": spaced,
                "country_code": parsed.country_code,
                "national_number": parsed.national_number,
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
    
    def _generate_messenger_links(self, phone: str, e164: str) -> List[Dict]:
        links = []
        for p in MESSENGER_PLATFORMS:
            url = p["url"].replace("{phone}", phone).replace("{e164}", e164)
            links.append({
                "name": p["name"],
                "url": url,
                "type": p["type"],
                "category": p["category"],
            })
        return links
    
    def _generate_lookup_links(self, phone: str, phone_local: str, region: str) -> List[Dict]:
        links = []
        for p in PHONE_LOOKUP_SERVICES:
            url = p["url"].replace("{phone}", phone).replace("{phone_local}", phone_local).replace("{region}", region.lower())
            links.append({
                "name": p["name"],
                "url": url,
                "type": p["type"],
                "category": p["category"],
            })
        return links
    
    def _generate_social_links(self, phone: str, phone_local: str) -> List[Dict]:
        links = []
        for p in SOCIAL_PHONE_SEARCH:
            url = p["url"].replace("{phone}", phone).replace("{phone_local}", phone_local)
            links.append({
                "name": p["name"],
                "url": url,
                "type": p["type"],
            })
        return links
    
    def _generate_indonesia_links(self, phone: str, phone_local: str) -> List[Dict]:
        links = []
        for p in INDONESIA_PHONE_SERVICES:
            url = p["url"].replace("{phone}", phone).replace("{phone_local}", phone_local)
            links.append({
                "name": p["name"],
                "url": url,
                "type": p["type"],
                "category": p["category"],
            })
        return links
    
    def _generate_google_dorks(self, phone: str, phone_local: str) -> List[Dict]:
        # Generate spaced version
        phone_spaced = " ".join([phone[i:i+4] for i in range(0, len(phone), 4)])
        
        dorks = []
        for d in GOOGLE_DORKS_PHONE:
            query = d["query"].replace("{phone}", phone).replace("{phone_local}", phone_local).replace("{phone_spaced}", phone_spaced)
            dorks.append({
                "name": d["name"],
                "query": query,
                "url": f"https://www.google.com/search?q={query.replace(' ', '+').replace('\"', '%22')}",
            })
        return dorks
    
    def _simulate_hlr(self, info: Dict) -> Dict[str, Any]:
        time.sleep(1)
        
        status = "Active (Simulated)"
        if info["type"] == "Mobile" and info["carrier"]:
            status = "Active - Mobile"
        elif info["type"] == "VoIP":
            status = "Active - VoIP/Virtual"
        elif info["type"] == "Landline":
            status = "Active - Landline"
        
        return {
            "status": status,
            "original_network": info.get("carrier", "Unknown"),
            "reachable": True,
            "roaming": "No",
            "ported": "Unknown",
            "note": "This is simulated HLR. Real HLR requires SS7 network access.",
        }


def scan_phone(phone: str, scan_mode: str = "quick") -> Dict[str, Any]:
    return PhoneLookup().scan(phone, scan_mode=scan_mode)
