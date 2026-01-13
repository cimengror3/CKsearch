"""
CKSEARCH - Image OSINT Module
==============================
Image/photo intelligence and analysis.
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console

import config
from core.scanner import BaseScanner
from core.api_client import APIClient

console = Console()


class ImageOSINT(BaseScanner):
    """Image OSINT scanner for photo analysis."""
    
    def __init__(self, language: str = "id"):
        super().__init__("Image OSINT", language)
        self.http_client = APIClient()
    
    def scan(self, image_path: str, **options) -> Dict[str, Any]:
        """
        Analyze image for OSINT data.
        
        Args:
            image_path: Path to image file or URL
        """
        self._start()
        
        results = {
            "source": image_path,
            "file_info": {},
            "exif_data": {},
            "geolocation": None,
            "hashes": {},
            "reverse_search_urls": [],
            "analysis": {},
        }
        
        # Check if URL or file
        is_url = image_path.startswith(('http://', 'https://'))
        
        if is_url:
            console.print("[cyan]→ Downloading image...[/cyan]")
            local_path = self._download_image(image_path)
            if not local_path:
                self._add_error("Failed to download image")
                self._finish()
                return {"error": "Failed to download image"}
        else:
            local_path = image_path
            if not os.path.exists(local_path):
                self._add_error("File not found")
                self._finish()
                return {"error": "File not found"}
        
        # File info
        console.print("[cyan]→ Getting file information...[/cyan]")
        results["file_info"] = self._get_file_info(local_path)
        
        # EXIF extraction
        console.print("[cyan]→ Extracting EXIF metadata...[/cyan]")
        results["exif_data"] = self._extract_exif(local_path)
        
        # GPS extraction
        if results["exif_data"].get("gps"):
            console.print("[cyan]→ Extracting GPS coordinates...[/cyan]")
            results["geolocation"] = self._extract_gps(results["exif_data"]["gps"])
        
        # Hash calculation
        console.print("[cyan]→ Calculating image hashes...[/cyan]")
        results["hashes"] = self._calculate_hashes(local_path)
        
        # Reverse image search URLs
        console.print("[cyan]→ Generating reverse search URLs...[/cyan]")
        results["reverse_search_urls"] = self._generate_reverse_search_urls(image_path if is_url else None)
        
        # Analysis summary
        results["analysis"] = self._analyze_image(results)
        
        self._finish()
        results["metadata"] = self.get_metadata()
        return results
    
    def _download_image(self, url: str) -> Optional[str]:
        """Download image from URL."""
        try:
            response = self.http_client.session.get(url, timeout=30)
            if response.status_code == 200:
                # Save to temp
                ext = url.split('.')[-1].split('?')[0][:4]
                filename = f"temp_image.{ext}" if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp'] else "temp_image.jpg"
                filepath = config.CACHE_DIR / filename
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return str(filepath)
        except Exception as e:
            self._add_warning(f"Download failed: {e}")
        return None
    
    def _get_file_info(self, filepath: str) -> Dict[str, Any]:
        """Get basic file information."""
        from PIL import Image
        
        info = {
            "filename": os.path.basename(filepath),
            "size_bytes": os.path.getsize(filepath),
            "size_human": self._human_size(os.path.getsize(filepath)),
        }
        
        try:
            with Image.open(filepath) as img:
                info["format"] = img.format
                info["mode"] = img.mode
                info["width"] = img.width
                info["height"] = img.height
                info["dimensions"] = f"{img.width}x{img.height}"
        except Exception as e:
            self._add_warning(f"Could not open image: {e}")
        
        return info
    
    def _extract_exif(self, filepath: str) -> Dict[str, Any]:
        """Extract EXIF metadata."""
        exif = {"raw": {}, "parsed": {}, "gps": None}
        
        try:
            import exifread
            
            with open(filepath, 'rb') as f:
                tags = exifread.process_file(f, details=True)
            
            # Parse important tags
            important_tags = {
                'Image Make': 'camera_make',
                'Image Model': 'camera_model',
                'EXIF DateTimeOriginal': 'date_taken',
                'EXIF DateTimeDigitized': 'date_digitized',
                'Image DateTime': 'date_modified',
                'EXIF ExposureTime': 'exposure_time',
                'EXIF FNumber': 'f_number',
                'EXIF ISOSpeedRatings': 'iso',
                'EXIF FocalLength': 'focal_length',
                'Image Software': 'software',
                'Image Artist': 'author',
                'Image Copyright': 'copyright',
                'EXIF LensModel': 'lens_model',
            }
            
            for tag, key in important_tags.items():
                if tag in tags:
                    exif["parsed"][key] = str(tags[tag])
            
            # GPS data
            gps_tags = {}
            for tag in tags:
                if 'GPS' in tag:
                    gps_tags[tag] = str(tags[tag])
            
            if gps_tags:
                exif["gps"] = gps_tags
            
            # Store all raw tags
            for tag in tags:
                if tag not in ['JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote']:
                    exif["raw"][tag] = str(tags[tag])
                    
        except Exception as e:
            self._add_warning(f"EXIF extraction failed: {e}")
        
        return exif
    
    def _extract_gps(self, gps_tags: Dict) -> Optional[Dict[str, Any]]:
        """Extract GPS coordinates from EXIF GPS tags."""
        try:
            lat_ref = gps_tags.get('GPS GPSLatitudeRef', 'N')
            lon_ref = gps_tags.get('GPS GPSLongitudeRef', 'E')
            lat = gps_tags.get('GPS GPSLatitude')
            lon = gps_tags.get('GPS GPSLongitude')
            
            if not lat or not lon:
                return None
            
            # Parse coordinates (format: [degrees, minutes, seconds])
            def parse_coord(coord_str: str) -> float:
                parts = coord_str.strip('[]').split(', ')
                if len(parts) == 3:
                    d = self._ratio_to_float(parts[0])
                    m = self._ratio_to_float(parts[1])
                    s = self._ratio_to_float(parts[2])
                    return d + m/60 + s/3600
                return 0.0
            
            latitude = parse_coord(lat)
            longitude = parse_coord(lon)
            
            if 'S' in lat_ref: latitude = -latitude
            if 'W' in lon_ref: longitude = -longitude
            
            return {
                "latitude": round(latitude, 6),
                "longitude": round(longitude, 6),
                "coordinates": f"{latitude:.6f}, {longitude:.6f}",
                "google_maps": f"https://www.google.com/maps?q={latitude},{longitude}",
                "openstreetmap": f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}&zoom=15",
            }
            
        except Exception as e:
            self._add_warning(f"GPS extraction failed: {e}")
            return None
    
    def _ratio_to_float(self, ratio_str: str) -> float:
        """Convert EXIF ratio string to float."""
        if '/' in ratio_str:
            num, den = ratio_str.split('/')
            return float(num) / float(den)
        return float(ratio_str)
    
    def _calculate_hashes(self, filepath: str) -> Dict[str, str]:
        """Calculate various hashes for the image."""
        hashes = {}
        
        with open(filepath, 'rb') as f:
            data = f.read()
            hashes["md5"] = hashlib.md5(data).hexdigest()
            hashes["sha1"] = hashlib.sha1(data).hexdigest()
            hashes["sha256"] = hashlib.sha256(data).hexdigest()
        
        return hashes
    
    def _generate_reverse_search_urls(self, image_url: str = None) -> List[Dict[str, str]]:
        """Generate reverse image search URLs."""
        urls = [
            {"engine": "Google Images", "url": "https://images.google.com/", "note": "Upload image manually"},
            {"engine": "TinEye", "url": "https://tineye.com/", "note": "Upload image manually"},
            {"engine": "Yandex Images", "url": "https://yandex.com/images/", "note": "Upload or paste URL"},
            {"engine": "Bing Visual Search", "url": "https://www.bing.com/visualsearch", "note": "Upload image"},
        ]
        
        if image_url:
            encoded = image_url.replace("&", "%26")
            urls.extend([
                {"engine": "Google (direct)", "url": f"https://www.google.com/searchbyimage?image_url={encoded}"},
                {"engine": "Yandex (direct)", "url": f"https://yandex.com/images/search?rpt=imageview&url={encoded}"},
            ])
        
        return urls
    
    def _analyze_image(self, results: Dict) -> Dict[str, Any]:
        """Analyze results and provide insights."""
        analysis = {
            "privacy_risk": "low",
            "findings": [],
            "recommendations": [],
        }
        
        # Check for GPS
        if results.get("geolocation"):
            analysis["privacy_risk"] = "high"
            analysis["findings"].append("Image contains GPS coordinates")
            analysis["recommendations"].append("Remove EXIF data before sharing")
        
        # Check for camera info
        exif = results.get("exif_data", {}).get("parsed", {})
        if exif.get("camera_make") or exif.get("camera_model"):
            analysis["findings"].append(f"Camera: {exif.get('camera_make', '')} {exif.get('camera_model', '')}")
        
        if exif.get("date_taken"):
            analysis["findings"].append(f"Photo taken: {exif.get('date_taken')}")
        
        if exif.get("software"):
            analysis["findings"].append(f"Edited with: {exif.get('software')}")
        
        return analysis
    
    def _human_size(self, size: int) -> str:
        """Convert bytes to human readable."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"


def analyze_image(path: str) -> Dict[str, Any]:
    """Quick image analysis function."""
    return ImageOSINT().scan(path)
