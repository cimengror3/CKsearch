# CKSEARCH - Professional OSINT Intelligence Tool

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20Android-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

```
   _____ _  __ _____ _____    _    ____   ____ _   _ 
  / ____| |/ // ____|  ___|  / \  |  _ \ / ___| | | |
 | |    | ' /| (___ | |_    / _ \ | |_) | |   | |_| |
 | |    |  <  \___ \|  _|  / ___ \|  _ <| |___|  _  |
 | |____| . \ ____) | |   /_/   \_\_| \_\\____|_| |_|
  \_____|_|\_\_____/|_|   By: CimenkDev
```

## 📋 Deskripsi

**CKSEARCH** adalah tools OSINT (Open Source Intelligence) profesional yang dirancang untuk investigasi digital. Tools ini mendukung multi-platform (Linux, Windows, Android/Termux) dengan arsitektur modular dan hasil yang akurat.

## ⚠️ Disclaimer

> **PERINGATAN**: Tools ini dibuat untuk tujuan **EDUKASI** dan **INVESTIGASI LEGAL** saja.
> - Penggunaan untuk kegiatan ilegal adalah **TERLARANG**
> - Pengguna bertanggung jawab penuh atas tindakannya
> - Developer tidak bertanggung jawab atas penyalahgunaan

## ✨ Fitur Utama

| # | Fitur | Deskripsi |
|---|-------|-----------|
| 1 | 📱 Phone Lookup | Analisis nomor telepon dengan Numverify API |
| 2 | 👤 Username Search | Pencarian username di 100+ platform |
| 3 | 📧 Email OSINT | Deteksi breach dengan XposedOrNot API |
| 4 | 🌐 Domain Intel | Analisis WHOIS, DNS, SSL, technology stack |
| 5 | 🖥️ IP Scanner | Passive & active scanning (seperti Nmap) |
| 6 | 🔎 Person OSINT | Pencarian berdasarkan nama lengkap |
| 7 | 🖼️ Image OSINT | EXIF extraction, GPS, reverse search |
| 8 | 📱 Social Deep Scan | Analisis mendalam profil social media |
| 9 | 📍 Geolocation | Analisis koordinat dan lokasi |

## 🚀 Instalasi

### Linux / Windows

```bash
# Clone repository
git clone https://github.com/CimenkDev/CKSEARCH.git
cd CKSEARCH

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

### Android (Termux)

```bash
# Install Python
pkg install python

# Clone dan install
git clone https://github.com/CimenkDev/CKSEARCH.git
cd CKSEARCH
pip install -r requirements.txt

# Run
python main.py
```

## 📖 Penggunaan

### Interactive Mode (Recommended)

```bash
python main.py
```

### Command Line Mode

```bash
# Phone lookup
python -m modules.phone_lookup +628123456789

# Username search
python -m modules.username_search johndoe

# Email OSINT
python -m modules.email_osint example@gmail.com

# Domain analysis
python -m modules.domain_intel example.com

# IP scan
python -m modules.ip_scanner 8.8.8.8
```

## 🔧 Konfigurasi

Edit `config.py` untuk mengatur API keys:

```python
API_KEYS = {
    "numverify": "YOUR_NUMVERIFY_API_KEY",
    "ipinfo": "YOUR_IPINFO_API_KEY",
    "xposedornot": None,  # Free, no key needed
}
```

## 📤 Format Output

- **Console** - Display langsung di terminal dengan formatting rich
- **JSON** - Export ke file JSON terstruktur
- **TXT/Markdown** - Export ke file teks/markdown
- **HTML** - Report profesional dengan dark theme
- **CSV** - Export data tabular ke CSV

## 📁 Struktur Proyek

```
CKSEARCH/
├── main.py              # Entry point
├── config.py            # Configuration
├── requirements.txt     # Dependencies
├── README.md            # Documentation
├── core/                # Core library
│   ├── banner.py        # ASCII art & UI
│   ├── language.py      # Multi-language support
│   ├── api_client.py    # API clients
│   ├── output.py        # Export handlers
│   └── scanner.py       # Base scanner
├── modules/             # OSINT modules
│   ├── phone_lookup.py
│   ├── username_search.py
│   ├── email_osint.py
│   ├── domain_intel.py
│   ├── ip_scanner.py
│   ├── person_osint.py
│   ├── image_osint.py
│   ├── social_deep.py
│   └── geolocation.py
└── output/              # Generated reports
```

## 🌐 Multi-Language Support

CKSEARCH mendukung:
- 🇮🇩 **Bahasa Indonesia**
- 🇺🇸 **English**

## 🔒 Keamanan

- Support Proxy/Tor untuk anonimitas
- Rate limiting untuk menghindari ban
- No data logging - data tidak disimpan

## 📊 API yang Digunakan

| API | Kegunaan | Free Tier |
|-----|----------|-----------|
| Numverify | Phone validation | ✅ 100 req/month |
| IPInfo | IP geolocation | ✅ 50K req/month |
| XposedOrNot | Email breach | ✅ Unlimited |

## 🤝 Contributing

Kontribusi selalu diterima! Silakan buat Pull Request atau Issue.

## 📄 License

MIT License - Lihat [LICENSE](LICENSE) untuk detail.

## 👨‍💻 Author

**CimenkDev**

---

⭐ **Star this repo if you find it useful!**
