"""
CKSEARCH - Geolocation OSINT Module
=====================================
Location intelligence and analysis.
"""

from typing import Dict, Any, List, Optional
from rich.console import Console

import config
from core.scanner import BaseScanner
from core.api_client import APIClient

console = Console()


class GeolocationOSINT(BaseScanner):
    """Geolocation intelligence scanner."""
    
    def __init__(self, language: str = "id"):
        super().__init__("Geolocation OSINT", language)
        self.http_client = APIClient()
    
    def scan(self, location: str, **options) -> Dict[str, Any]:
        """
        Analyze location data.
        
        Args:
            location: Coordinates (lat,lng), address, or place name
        """
        self._start()
        
        results = {
            "input": location,
            "coordinates": None,
            "address": None,
            "maps": {},
            "nearby_search": [],
            "satellite_imagery": [],
            "osint_links": [],
        }
        
        # Parse input
        console.print("[cyan]→ Parsing location input...[/cyan]")
        coords = self._parse_location(location)
        
        if coords:
            results["coordinates"] = coords
            
            # Generate map links
            console.print("[cyan]→ Generating map links...[/cyan]")
            results["maps"] = self._generate_map_links(coords["lat"], coords["lng"])
            
            # Satellite imagery
            console.print("[cyan]→ Generating satellite imagery links...[/cyan]")
            results["satellite_imagery"] = self._generate_satellite_links(coords["lat"], coords["lng"])
            
            # OSINT links
            console.print("[cyan]→ Generating OSINT research links...[/cyan]")
            results["osint_links"] = self._generate_osint_links(coords["lat"], coords["lng"])
            
            # Nearby searches
            console.print("[cyan]→ Generating nearby search links...[/cyan]")
            results["nearby_search"] = self._generate_nearby_search(coords["lat"], coords["lng"])
        else:
            # Treat as address/place name
            results["address"] = location
            results["geocoding_links"] = self._generate_geocoding_links(location)
        
        self._finish()
        results["metadata"] = self.get_metadata()
        return results
    
    def _parse_location(self, location: str) -> Optional[Dict[str, float]]:
        """Parse location string to coordinates."""
        import re
        
        # Try to parse as coordinates
        patterns = [
            r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)',  # lat,lng
            r'(-?\d+\.?\d*)\s+(-?\d+\.?\d*)',    # lat lng
        ]
        
        for pattern in patterns:
            match = re.match(pattern, location.strip())
            if match:
                lat, lng = float(match.group(1)), float(match.group(2))
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    return {"lat": lat, "lng": lng}
        
        return None
    
    def _generate_map_links(self, lat: float, lng: float) -> Dict[str, str]:
        """Generate various map service links."""
        return {
            "google_maps": f"https://www.google.com/maps?q={lat},{lng}",
            "google_street_view": f"https://www.google.com/maps/@{lat},{lng},3a,75y,0h,90t/data=!3m6!1e1!3m4",
            "openstreetmap": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lng}&zoom=15",
            "bing_maps": f"https://www.bing.com/maps?cp={lat}~{lng}&lvl=15",
            "apple_maps": f"https://maps.apple.com/?ll={lat},{lng}&z=15",
            "yandex_maps": f"https://yandex.com/maps/?ll={lng},{lat}&z=15",
            "here_maps": f"https://wego.here.com/?map={lat},{lng},15,normal",
            "waze": f"https://www.waze.com/ul?ll={lat},{lng}&zoom=15",
        }
    
    def _generate_satellite_links(self, lat: float, lng: float) -> List[Dict[str, str]]:
        """Generate satellite imagery links."""
        return [
            {"service": "Google Earth Web", "url": f"https://earth.google.com/web/@{lat},{lng},0a,1000d,35y,0h,0t,0r"},
            {"service": "Sentinel Hub", "url": f"https://apps.sentinel-hub.com/eo-browser/?zoom=14&lat={lat}&lng={lng}"},
            {"service": "NASA Worldview", "url": f"https://worldview.earthdata.nasa.gov/?v={lng-0.5},{lat-0.5},{lng+0.5},{lat+0.5}"},
            {"service": "Zoom Earth", "url": f"https://zoom.earth/#{lat},{lng},15z"},
            {"service": "SkyFi", "url": f"https://app.skyfi.com/explore?lat={lat}&lng={lng}"},
        ]
    
    def _generate_osint_links(self, lat: float, lng: float) -> List[Dict[str, str]]:
        """Generate OSINT research links."""
        return [
            {"tool": "What3Words", "url": f"https://what3words.com/{lat},{lng}"},
            {"tool": "GeoGuessr", "url": f"https://www.geoguessr.com/maps/world/play?lat={lat}&lng={lng}"},
            {"tool": "SunCalc (Sun position)", "url": f"https://www.suncalc.org/#/{lat},{lng},15/null/null/null/null"},
            {"tool": "FlightRadar24", "url": f"https://www.flightradar24.com/{lat},{lng}/12"},
            {"tool": "MarineTraffic", "url": f"https://www.marinetraffic.com/en/ais/home/centerx:{lng}/centery:{lat}/zoom:12"},
            {"tool": "OpenRailwayMap", "url": f"https://www.openrailwaymap.org/?lat={lat}&lon={lng}&zoom=13"},
            {"tool": "Wigle (WiFi Map)", "url": f"https://wigle.net/map?lat={lat}&lon={lng}"},
            {"tool": "OpenCellID", "url": f"https://www.opencellid.org/#zoom=15&lat={lat}&lon={lng}"},
        ]
    
    def _generate_nearby_search(self, lat: float, lng: float) -> List[Dict[str, str]]:
        """Generate nearby search links."""
        return [
            {"type": "Social Media (Instagram)", "url": f"https://www.instagram.com/explore/locations/{lat},{lng}/"},
            {"type": "Flickr Photos", "url": f"https://www.flickr.com/map?&fLat={lat}&fLon={lng}&zl=14"},
            {"type": "Twitter/X Search", "url": f"https://twitter.com/search?q=geocode:{lat},{lng},1km"},
            {"type": "Google Images", "url": f"https://www.google.com/search?q=near:{lat},{lng}&tbm=isch"},
            {"type": "Foursquare", "url": f"https://foursquare.com/explore?ll={lat},{lng}"},
            {"type": "Yelp", "url": f"https://www.yelp.com/search?find_loc={lat},{lng}"},
            {"type": "TripAdvisor", "url": f"https://www.tripadvisor.com/Attractions-g-Activities-a_geo.{lat}~{lng}.html"},
        ]
    
    def _generate_geocoding_links(self, address: str) -> List[Dict[str, str]]:
        """Generate geocoding service links for address lookup."""
        encoded = address.replace(" ", "+")
        
        return [
            {"service": "Google Maps", "url": f"https://www.google.com/maps/search/{encoded}"},
            {"service": "OpenStreetMap Nominatim", "url": f"https://nominatim.openstreetmap.org/search?q={encoded}"},
            {"service": "Bing Maps", "url": f"https://www.bing.com/maps?q={encoded}"},
            {"service": "Here Maps", "url": f"https://wego.here.com/search/{encoded}"},
        ]


def analyze_location(location: str) -> Dict[str, Any]:
    """Quick location analysis function."""
    return GeolocationOSINT().scan(location)
