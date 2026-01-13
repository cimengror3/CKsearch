"""
CKSEARCH - Language Module
===========================
Multi-language support untuk interface.
"""

from typing import Dict, Any


class Language:
    """Class untuk mengelola multi-language support."""
    
    # Language data
    LANGUAGES: Dict[str, Dict[str, Any]] = {
        "id": {
            "name": "Bahasa Indonesia",
            "flag": "🇮🇩",
            
            # Menu utama
            "select_language": "Pilih Bahasa / Select Language",
            "main_menu": "MENU UTAMA",
            "select_option": "Pilih opsi",
            "enter_choice": "Masukkan pilihan Anda",
            "invalid_choice": "Pilihan tidak valid! Silakan coba lagi.",
            "back": "Kembali",
            "exit": "Keluar",
            "exit_confirm": "Apakah Anda yakin ingin keluar?",
            "goodbye": "Terima kasih telah menggunakan CKSEARCH!",
            
            # Menu fitur
            "menu_phone": "Cari Berdasarkan Nomor HP",
            "menu_username": "Cari Berdasarkan Username",
            "menu_email": "Cari Berdasarkan Email",
            "menu_domain": "Cari Berdasarkan Domain",
            "menu_ip": "Cari Berdasarkan IP/Server",
            "menu_person": "Cari Berdasarkan Nama (Person OSINT)",
            "menu_image": "Analisis Gambar/Foto (Image OSINT)",
            "menu_social": "Deep Scan Social Media",
            "menu_geolocation": "Geolocation Intelligence",
            "menu_settings": "Pengaturan",
            
            # Input prompts
            "enter_phone": "Masukkan nomor telepon (format internasional, contoh: +628123456789)",
            "enter_username": "Masukkan username yang ingin dicari",
            "enter_email": "Masukkan alamat email",
            "enter_domain": "Masukkan nama domain (contoh: example.com)",
            "enter_ip": "Masukkan alamat IP",
            "enter_name": "Masukkan nama lengkap",
            "enter_image_path": "Masukkan path file gambar atau URL",
            "enter_social_url": "Masukkan URL profil social media",
            "enter_coordinates": "Masukkan koordinat (latitude, longitude)",
            
            # Scanner options
            "scan_type": "Pilih tipe scan",
            "passive_scan": "Passive Scan (Aman, tidak terdeteksi)",
            "active_scan": "Active Scan (Lebih lengkap, terdeteksi)",
            "both_scan": "Keduanya",
            
            # Output
            "select_output": "Pilih format output",
            "output_display": "Tampilkan di layar saja",
            "output_json": "Export ke JSON",
            "output_txt": "Export ke TXT/Markdown",
            "output_html": "Export ke HTML Report",
            "output_csv": "Export ke CSV",
            "output_all": "Semua format",
            "output_saved": "Hasil disimpan ke",
            
            # Status messages
            "searching": "Mencari",
            "scanning": "Memindai",
            "analyzing": "Menganalisis",
            "processing": "Memproses",
            "please_wait": "Mohon tunggu...",
            "completed": "Selesai!",
            "found": "Ditemukan",
            "not_found": "Tidak ditemukan",
            "error": "Terjadi kesalahan",
            "no_results": "Tidak ada hasil",
            
            # Results
            "results": "HASIL PENCARIAN",
            "summary": "Ringkasan",
            "details": "Detail",
            "total_found": "Total ditemukan",
            "platforms_checked": "Platform diperiksa",
            "time_taken": "Waktu yang dibutuhkan",
            
            # Phone results
            "phone_valid": "Nomor Valid",
            "phone_country": "Negara",
            "phone_carrier": "Operator",
            "phone_type": "Tipe Nomor",
            "phone_location": "Lokasi",
            "phone_timezone": "Zona Waktu",
            
            # Email results
            "email_valid": "Email Valid",
            "email_breached": "Terdeteksi dalam Breach",
            "breach_count": "Jumlah Breach",
            "breach_details": "Detail Breach",
            
            # Domain results
            "domain_registrar": "Registrar",
            "domain_created": "Tanggal Dibuat",
            "domain_expires": "Tanggal Kadaluarsa",
            "domain_nameservers": "Nameservers",
            "domain_dns": "DNS Records",
            "domain_ssl": "SSL Certificate",
            "domain_tech": "Technology Stack",
            
            # IP results
            "ip_location": "Lokasi",
            "ip_isp": "ISP",
            "ip_asn": "ASN",
            "ip_org": "Organisasi",
            "ip_ports": "Port Terbuka",
            "ip_services": "Layanan Terdeteksi",
            
            # Settings
            "settings_api": "Konfigurasi API Keys",
            "settings_proxy": "Pengaturan Proxy/Tor",
            "settings_output": "Pengaturan Output",
            "settings_language": "Ganti Bahasa",
        },
        
        "en": {
            "name": "English",
            "flag": "🇺🇸",
            
            # Main menu
            "select_language": "Select Language",
            "main_menu": "MAIN MENU",
            "select_option": "Select option",
            "enter_choice": "Enter your choice",
            "invalid_choice": "Invalid choice! Please try again.",
            "back": "Back",
            "exit": "Exit",
            "exit_confirm": "Are you sure you want to exit?",
            "goodbye": "Thank you for using CKSEARCH!",
            
            # Feature menu
            "menu_phone": "Search by Phone Number",
            "menu_username": "Search by Username",
            "menu_email": "Search by Email",
            "menu_domain": "Search by Domain",
            "menu_ip": "Search by IP/Server",
            "menu_person": "Search by Name (Person OSINT)",
            "menu_image": "Image/Photo Analysis (Image OSINT)",
            "menu_social": "Deep Scan Social Media",
            "menu_geolocation": "Geolocation Intelligence",
            "menu_settings": "Settings",
            
            # Input prompts
            "enter_phone": "Enter phone number (international format, e.g., +628123456789)",
            "enter_username": "Enter username to search",
            "enter_email": "Enter email address",
            "enter_domain": "Enter domain name (e.g., example.com)",
            "enter_ip": "Enter IP address",
            "enter_name": "Enter full name",
            "enter_image_path": "Enter image file path or URL",
            "enter_social_url": "Enter social media profile URL",
            "enter_coordinates": "Enter coordinates (latitude, longitude)",
            
            # Scanner options
            "scan_type": "Select scan type",
            "passive_scan": "Passive Scan (Safe, undetected)",
            "active_scan": "Active Scan (More complete, detected)",
            "both_scan": "Both",
            
            # Output
            "select_output": "Select output format",
            "output_display": "Display on screen only",
            "output_json": "Export to JSON",
            "output_txt": "Export to TXT/Markdown",
            "output_html": "Export to HTML Report",
            "output_csv": "Export to CSV",
            "output_all": "All formats",
            "output_saved": "Results saved to",
            
            # Status messages
            "searching": "Searching",
            "scanning": "Scanning",
            "analyzing": "Analyzing",
            "processing": "Processing",
            "please_wait": "Please wait...",
            "completed": "Completed!",
            "found": "Found",
            "not_found": "Not found",
            "error": "An error occurred",
            "no_results": "No results",
            
            # Results
            "results": "SEARCH RESULTS",
            "summary": "Summary",
            "details": "Details",
            "total_found": "Total found",
            "platforms_checked": "Platforms checked",
            "time_taken": "Time taken",
            
            # Phone results
            "phone_valid": "Valid Number",
            "phone_country": "Country",
            "phone_carrier": "Carrier",
            "phone_type": "Number Type",
            "phone_location": "Location",
            "phone_timezone": "Timezone",
            
            # Email results
            "email_valid": "Valid Email",
            "email_breached": "Found in Breach",
            "breach_count": "Breach Count",
            "breach_details": "Breach Details",
            
            # Domain results
            "domain_registrar": "Registrar",
            "domain_created": "Created Date",
            "domain_expires": "Expiry Date",
            "domain_nameservers": "Nameservers",
            "domain_dns": "DNS Records",
            "domain_ssl": "SSL Certificate",
            "domain_tech": "Technology Stack",
            
            # IP results
            "ip_location": "Location",
            "ip_isp": "ISP",
            "ip_asn": "ASN",
            "ip_org": "Organization",
            "ip_ports": "Open Ports",
            "ip_services": "Detected Services",
            
            # Settings
            "settings_api": "API Keys Configuration",
            "settings_proxy": "Proxy/Tor Settings",
            "settings_output": "Output Settings",
            "settings_language": "Change Language",
        }
    }
    
    def __init__(self, language: str = "id"):
        """
        Initialize language manager.
        
        Args:
            language: Language code ("id" or "en")
        """
        self.current = language if language in self.LANGUAGES else "id"
    
    def get(self, key: str, default: str = "") -> str:
        """
        Get translated string.
        
        Args:
            key: Translation key
            default: Default value if key not found
            
        Returns:
            Translated string
        """
        return self.LANGUAGES[self.current].get(key, default or key)
    
    def set_language(self, language: str) -> bool:
        """
        Set current language.
        
        Args:
            language: Language code
            
        Returns:
            True if successful, False if language not supported
        """
        if language in self.LANGUAGES:
            self.current = language
            return True
        return False
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get list of available languages with their flags."""
        return {
            code: f"{data['flag']} {data['name']}"
            for code, data in self.LANGUAGES.items()
        }
    
    def __call__(self, key: str, default: str = "") -> str:
        """Shorthand for get()."""
        return self.get(key, default)


# Global instance
LANG = Language()


def set_language(language: str) -> bool:
    """Set global language."""
    return LANG.set_language(language)


def t(key: str, default: str = "") -> str:
    """Translate function shorthand."""
    return LANG.get(key, default)


if __name__ == "__main__":
    # Test language module
    print("Testing Indonesian:")
    LANG.set_language("id")
    print(f"  Main menu: {LANG('main_menu')}")
    print(f"  Phone: {LANG('menu_phone')}")
    
    print("\nTesting English:")
    LANG.set_language("en")
    print(f"  Main menu: {LANG('main_menu')}")
    print(f"  Phone: {LANG('menu_phone')}")
