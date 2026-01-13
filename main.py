#!/usr/bin/env python3
"""
CKSEARCH - Professional OSINT Intelligence Tool
=================================================
By: CimenkDev

Multi-platform OSINT tool for cybersecurity professionals.
Supports: Linux, Windows, Android (Termux)

Features three tiers:
- FREE: 5 requests/day (auto-assigned)
- PREMIUM: Unlimited (license key required)
- ADMIN: Full access
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich import box
from datetime import datetime, timedelta

import config
from core.banner import Banner
from core.language import LANG, set_language
from core.output import OutputManager

console = Console()


class CKSearch:
    """Main CKSEARCH application class with license system."""
    
    def __init__(self):
        self.language = config.DEFAULT_LANGUAGE
        self.output_manager = OutputManager()
        self.license_info = None
        self.license_client = None
    
    def run(self):
        """Run the main application."""
        try:
            # Initialize license client
            self._init_license()
            
            # Check CLI arguments first
            from cli import parse_args, is_interactive_mode, get_scan_target
            args = parse_args()
            
            # Handle special commands
            if args.status:
                self._show_license_status()
                return
            
            if args.activate:
                self._activate_license(args.activate)
                return
            
            if args.referral:
                self._use_referral(args.referral)
                return
            
            # CLI mode or interactive mode
            if not is_interactive_mode(args):
                self._run_cli_mode(args)
            else:
                self._run_interactive_mode()
                
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted by user[/yellow]")
            self._exit()
    
    def _init_license(self):
        """Initialize license client and validate."""
        try:
            from core.license import get_license_client
            self.license_client = get_license_client()
            
            console.print("[dim]Validating license...[/dim]", end="\r")
            self.license_info = self.license_client.validate()
            console.print(" " * 30, end="\r")  # Clear line
            
            # Check maintenance mode
            if self.license_info.maintenance_mode:
                console.print(Panel(
                    f"[yellow]⚠ MAINTENANCE MODE[/yellow]\n\n{self.license_info.maintenance_message or 'System under maintenance.'}",
                    border_style="yellow"
                ))
                sys.exit(0)
            
            # Check if banned
            if self.license_info.is_banned:
                console.print(Panel(
                    f"[red]⛔ ACCOUNT BANNED[/red]\n\nReason: {self.license_info.ban_reason or 'Violation of terms.'}\n\nContact: {self.license_info.contact_info}",
                    border_style="red"
                ))
                sys.exit(1)
            
            # Show broadcast message
            if self.license_info.broadcast_message:
                console.print(Panel(
                    f"[cyan]📢 Announcement[/cyan]\n\n{self.license_info.broadcast_message}",
                    border_style="cyan"
                ))
            
            # Show update notification
            if self.license_info.update_available:
                console.print(f"[yellow]⚡ Update available! Download: {self.license_info.update_url}[/yellow]\n")
            
        except Exception as e:
            console.print(f"[dim]License check skipped: {e}[/dim]")
            self.license_info = None
    
    def _check_limit(self, module: str = "general") -> bool:
        """
        Check if user has remaining requests.
        Returns True if can proceed, False otherwise.
        """
        if not self.license_info:
            return True  # Offline mode
        
        # Unlimited for premium/admin
        if self.license_info.tier in ["premium", "admin"]:
            return True
        
        # Username is unlimited for free tier (Quick only)
        if module == "username":
            return True
        
        # Check remaining
        if self.license_info.remaining_requests <= 0:
            self._show_limit_exceeded()
            return False
        
        return True
    
    def _show_limit_exceeded(self):
        """Show limit exceeded message with upgrade info."""
        reset_time = "00:00 WIB"
        if self.license_info and self.license_info.reset_at:
            # Calculate time until reset
            now = datetime.utcnow()
            reset = self.license_info.reset_at.replace(tzinfo=None)
            delta = reset - now
            if delta.total_seconds() > 0:
                hours = int(delta.total_seconds() // 3600)
                minutes = int((delta.total_seconds() % 3600) // 60)
                reset_time = f"{hours} jam {minutes} menit"
        
        message = f"""
[red]⚠️ Limit harian Anda sudah habis![/red]
   Tersisa: 0/{self.license_info.daily_limit if self.license_info else 5} request

[cyan]📅 Reset dalam:[/cyan] {reset_time} (00:00 WIB)

[yellow]💎 Upgrade ke Premium untuk unlimited access![/yellow]
   Chat: {self.license_info.contact_info if self.license_info else '@cimenk'} (Telegram)
   
   [bold]Paket Premium:[/bold]
   • 7 Hari  - [Hubungi Admin]
   • 14 Hari - [Hubungi Admin]
   • 30 Hari - [Hubungi Admin]
   • 1 Tahun - [Hubungi Admin]

[dim]Kode Referral Anda: {self.license_info.referral_code if self.license_info else 'N/A'}[/dim]
[dim]Share untuk dapat +1 request/hari![/dim]
"""
        console.print(Panel(message.strip(), title="Limit Exceeded", border_style="red"))
    
    def _show_license_status(self):
        """Show current license status."""
        Banner.show(self.language)
        
        if not self.license_info:
            console.print("[yellow]Unable to check license status (offline)[/yellow]")
            return
        
        tier_colors = {
            "free": "white",
            "premium": "green",
            "admin": "magenta",
        }
        tier_color = tier_colors.get(self.license_info.tier, "white")
        
        table = Table(title="📜 License Status", box=box.ROUNDED)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Tier", f"[{tier_color}]{self.license_info.tier.upper()}[/{tier_color}]")
        
        if self.license_info.tier in ["premium", "admin"]:
            table.add_row("Requests", "[green]UNLIMITED[/green]")
        else:
            table.add_row("Remaining Today", f"{self.license_info.remaining_requests}/{self.license_info.daily_limit}")
            if self.license_info.extra_requests > 0:
                table.add_row("Bonus Requests", f"+{self.license_info.extra_requests}/day")
        
        if self.license_info.expires_at:
            exp = self.license_info.expires_at.strftime("%Y-%m-%d %H:%M")
            table.add_row("Expires", exp)
        
        table.add_row("Referral Code", self.license_info.referral_code or "N/A")
        table.add_row("Contact", self.license_info.contact_info)
        
        console.print(table)
        
        # Show fingerprint for support
        from core.fingerprint import get_fingerprint_short
        console.print(f"\n[dim]Device ID: {get_fingerprint_short()}[/dim]")
    
    def _activate_license(self, key: str):
        """Activate a license key."""
        Banner.show(self.language)
        console.print("[cyan]Activating license...[/cyan]")
        
        if not self.license_client:
            console.print("[red]Unable to connect to license server[/red]")
            return
        
        result = self.license_client.activate(key)
        
        if result.get("success"):
            console.print(f"\n[green]✓ {result.get('message')}[/green]")
            console.print("\n[dim]Restart CKSEARCH untuk menikmati fitur premium![/dim]")
        else:
            console.print(f"\n[red]✗ {result.get('message')}[/red]")
    
    def _use_referral(self, code: str):
        """Use a referral code."""
        Banner.show(self.language)
        console.print("[cyan]Applying referral code...[/cyan]")
        
        if not self.license_client:
            console.print("[red]Unable to connect to license server[/red]")
            return
        
        result = self.license_client.use_referral(code)
        
        if result.get("success"):
            console.print(f"\n[green]✓ {result.get('message')}[/green]")
        else:
            console.print(f"\n[red]✗ {result.get('message')}[/red]")
    
    def _log_usage(self, module: str, target: str = None, scan_mode: str = None, success: bool = True):
        """Log usage to server and decrement counter."""
        if self.license_client:
            try:
                result = self.license_client.log_telemetry(
                    module=module,
                    target=target,
                    scan_mode=scan_mode,
                    success=success,
                )
                # Update remaining count
                if self.license_info and "remaining_requests" in result:
                    self.license_info.remaining_requests = result.get("remaining_requests", 0)
            except:
                pass
    
    def _run_cli_mode(self, args):
        """Run in CLI mode with arguments."""
        from cli import get_scan_target
        
        scan_type, target = get_scan_target(args)
        if not scan_type:
            console.print("[red]No target specified[/red]")
            return
        
        scan_mode = "deep" if args.deep else "quick"
        
        # Check limit (username is exempt)
        if not self._check_limit(scan_type):
            return
        
        # Run scan
        results = self._run_scan(scan_type, target, scan_mode)
        
        if results:
            # Log usage
            self._log_usage(scan_type, target, scan_mode)
            
            # Output
            if args.output == "json":
                self.output_manager.export_json(results, prefix=scan_type)
            elif args.output == "txt":
                self.output_manager.export_txt(results, prefix=scan_type)
            elif args.output == "html":
                self.output_manager.export_html(results, prefix=scan_type, title=scan_type)
            elif args.output == "all":
                self.output_manager.export_all(results, prefix=scan_type, title=scan_type)
            else:
                self.output_manager.display_console(results, scan_type)
            
            # PDF export
            if args.pdf:
                from core.pdf_export import generate_pdf_report
                pdf_path = generate_pdf_report(results, f"{scan_type} - {target}")
                console.print(f"\n[green]PDF Report saved: {pdf_path}[/green]")
    
    def _run_scan(self, scan_type: str, target: str, scan_mode: str = "quick") -> dict:
        """Run a scan and return results."""
        scanners = {
            "phone": ("modules.phone_lookup", "PhoneLookup"),
            "email": ("modules.email_osint", "EmailOSINT"),
            "username": ("modules.username_search", "UsernameSearch"),
            "domain": ("modules.domain_intel", "DomainIntel"),
            "ip": ("modules.ip_scanner", "IPScanner"),
            "name": ("modules.person_osint", "PersonOSINT"),
            "image": ("modules.image_osint", "ImageOSINT"),
            "social": ("modules.social_deep", "SocialDeepScan"),
            "geo": ("modules.geolocation", "GeolocationOSINT"),
        }
        
        if scan_type not in scanners:
            console.print(f"[red]Unknown scan type: {scan_type}[/red]")
            return {}
        
        module_path, class_name = scanners[scan_type]
        
        try:
            import importlib
            module = importlib.import_module(module_path)
            scanner_class = getattr(module, class_name)
            
            scanner = scanner_class(self.language)
            
            # Check if premium needed for deep scan
            if scan_mode == "deep" and self.license_info:
                if self.license_info.tier == "free" and scan_type != "username":
                    console.print("[yellow]⚠ Deep Scan requires Premium. Using Quick Scan.[/yellow]")
                    scan_mode = "quick"
            
            return scanner.scan(target, scan_mode=scan_mode)
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return {}
    
    def _run_interactive_mode(self):
        """Run in interactive mode with menu."""
        # Show banner and language selection
        self._show_banner_and_select_language()
        
        # Main loop
        while True:
            choice = self._show_main_menu()
            
            if choice == "0":
                self._exit()
                break
            
            self._handle_choice(choice)
    
    def _show_banner_and_select_language(self):
        """Show banner and language selection."""
        Banner.show(self.language)
        
        # Show tier badge
        if self.license_info:
            tier = self.license_info.tier.upper()
            tier_colors = {"FREE": "white", "PREMIUM": "green", "ADMIN": "magenta"}
            color = tier_colors.get(tier, "white")
            
            remaining = "∞" if tier != "FREE" else f"{self.license_info.remaining_requests}/{self.license_info.daily_limit}"
            console.print(f"[{color}]🔑 {tier}[/{color}] | Requests: {remaining}\n")
        
        # Language selection
        console.print("[bold cyan]Select Language / Pilih Bahasa:[/bold cyan]")
        console.print("[1] 🇮🇩 Bahasa Indonesia")
        console.print("[2] 🇺🇸 English")
        
        choice = Prompt.ask("Choice", choices=["1", "2"], default="1")
        
        if choice == "1":
            self.language = "id"
        else:
            self.language = "en"
        
        set_language(self.language)
        console.clear()
        Banner.show(self.language)
        
        # Show tier badge again after clear
        if self.license_info:
            tier = self.license_info.tier.upper()
            tier_colors = {"FREE": "white", "PREMIUM": "green", "ADMIN": "magenta"}
            color = tier_colors.get(tier, "white")
            remaining = "∞" if tier != "FREE" else f"{self.license_info.remaining_requests}/{self.license_info.daily_limit}"
            console.print(f"[{color}]🔑 {tier}[/{color}] | Requests: {remaining}\n")
    
    def _show_main_menu(self) -> str:
        """Show main menu and get user choice."""
        console.print()
        
        table = Table(
            title=f"🔍 {LANG('main_menu')}",
            box=box.ROUNDED,
            show_header=False,
            border_style="cyan",
        )
        table.add_column("Option", style="bold cyan", width=3)
        table.add_column("Feature", style="white")
        
        menu_items = [
            ("1", LANG("menu_phone"), "📱"),
            ("2", LANG("menu_username"), "👤"),
            ("3", LANG("menu_email"), "📧"),
            ("4", LANG("menu_domain"), "🌐"),
            ("5", LANG("menu_ip"), "🖥️"),
            ("6", LANG("menu_person"), "🔎"),
            ("7", LANG("menu_image"), "🖼️"),
            ("8", LANG("menu_social"), "📱"),
            ("9", LANG("menu_geolocation"), "📍"),
            ("0", LANG("exit"), "🚪"),
        ]
        
        for num, text, icon in menu_items:
            table.add_row(f"[{num}]", f"{icon} {text}")
        
        console.print(table)
        console.print()
        
        return Prompt.ask(
            LANG("enter_choice"),
            choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
            default="1"
        )
    
    def _handle_choice(self, choice: str):
        """Handle menu choice."""
        handlers = {
            "1": self._phone_lookup,
            "2": self._username_search,
            "3": self._email_osint,
            "4": self._domain_intel,
            "5": self._ip_scanner,
            "6": self._person_osint,
            "7": self._image_osint,
            "8": self._social_deep,
            "9": self._geolocation,
        }
        
        handler = handlers.get(choice)
        if handler:
            try:
                handler()
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
        
        # Pause before returning to menu
        console.print()
        Prompt.ask(f"[dim]{LANG('back')}[/dim]", default="")
        console.clear()
        Banner.show(self.language)
        
        # Show tier badge
        if self.license_info:
            tier = self.license_info.tier.upper()
            tier_colors = {"FREE": "white", "PREMIUM": "green", "ADMIN": "magenta"}
            color = tier_colors.get(tier, "white")
            remaining = "∞" if tier != "FREE" else f"{self.license_info.remaining_requests}/{self.license_info.daily_limit}"
            console.print(f"[{color}]🔑 {tier}[/{color}] | Requests: {remaining}\n")
    
    def _phone_lookup(self):
        """Phone number lookup."""
        if not self._check_limit("phone"):
            return
        
        Banner.show_module_header(LANG("menu_phone"), "📱")
        
        phone = Prompt.ask(LANG("enter_phone"))
        if not phone:
            return
        
        # Ask scan mode
        mode_choice = Prompt.ask(
            "\n[cyan]Scan Mode:[/cyan]\n[1] Quick Scan\n[2] Deep Scan",
            choices=["1", "2"],
            default="1"
        )
        mode = "deep" if mode_choice == "2" else "quick"
        
        # Check premium for deep
        if mode == "deep" and self.license_info and self.license_info.tier == "free":
            console.print("[yellow]⚠ Deep Scan requires Premium. Using Quick Scan.[/yellow]")
            mode = "quick"
        
        from modules.phone_lookup import PhoneLookup
        
        scanner = PhoneLookup(self.language)
        results = scanner.scan(phone, scan_mode=mode)
        
        # Log usage
        self._log_usage("phone", phone, mode)
        
        self._display_and_export(results, "phone_lookup", LANG("menu_phone"))
    
    def _username_search(self):
        """Username search - FREE users get unlimited Quick, Premium only for Deep."""
        Banner.show_module_header(LANG("menu_username"), "👤")
        
        username = Prompt.ask(LANG("enter_username"))
        if not username:
            return
        
        # Ask scan mode
        mode_choice = Prompt.ask(
            "\n[cyan]Scan Mode:[/cyan]\n[1] Quick Scan (75 sites) - FREE\n[2] Deep Scan (271 sites) - PREMIUM",
            choices=["1", "2"],
            default="1"
        )
        mode = "deep" if mode_choice == "2" else "quick"
        
        # Check premium for deep
        if mode == "deep" and self.license_info and self.license_info.tier == "free":
            console.print("[yellow]⚠ Deep Scan (271 sites) requires Premium. Using Quick Scan (75 sites).[/yellow]")
            mode = "quick"
        
        from modules.username_search import UsernameSearch
        
        scanner = UsernameSearch(self.language)
        results = scanner.scan(username, scan_mode=mode)
        
        # Display summary
        if results.get("found"):
            console.print(f"\n[green]✓ {LANG('found')} on {len(results['found'])} platforms:[/green]")
            for item in results["found"][:20]:
                console.print(f"  [{item['category']}] {item['site']}: {item['url']}")
            if len(results["found"]) > 20:
                console.print(f"  [dim]... and {len(results['found']) - 20} more[/dim]")
        
        self._display_and_export(results, "username_search", LANG("menu_username"))
    
    def _email_osint(self):
        """Email OSINT."""
        if not self._check_limit("email"):
            return
        
        Banner.show_module_header(LANG("menu_email"), "📧")
        
        email = Prompt.ask(LANG("enter_email"))
        if not email:
            return
        
        mode_choice = Prompt.ask(
            "\n[cyan]Scan Mode:[/cyan]\n[1] Quick Scan\n[2] Deep Scan",
            choices=["1", "2"],
            default="1"
        )
        mode = "deep" if mode_choice == "2" else "quick"
        
        if mode == "deep" and self.license_info and self.license_info.tier == "free":
            console.print("[yellow]⚠ Deep Scan requires Premium. Using Quick Scan.[/yellow]")
            mode = "quick"
        
        from modules.email_osint import EmailOSINT
        
        scanner = EmailOSINT(self.language)
        results = scanner.scan(email, scan_mode=mode)
        
        # Log usage
        self._log_usage("email", email, mode)
        
        # Display breach summary
        breaches = results.get("breaches", {})
        if breaches.get("found"):
            console.print(f"\n[red]⚠ {LANG('email_breached')}: {breaches['count']} breaches[/red]")
            for breach in breaches.get("details", [])[:5]:
                console.print(f"  • {breach.get('name', 'Unknown')}")
        else:
            console.print(f"\n[green]✓ No breaches found[/green]")
        
        self._display_and_export(results, "email_osint", LANG("menu_email"))
    
    def _domain_intel(self):
        """Domain intelligence."""
        if not self._check_limit("domain"):
            return
        
        Banner.show_module_header(LANG("menu_domain"), "🌐")
        
        domain = Prompt.ask(LANG("enter_domain"))
        if not domain:
            return
        
        mode_choice = Prompt.ask(
            "\n[cyan]Scan Mode:[/cyan]\n[1] Quick Scan\n[2] Deep Scan",
            choices=["1", "2"],
            default="1"
        )
        mode = "deep" if mode_choice == "2" else "quick"
        
        if mode == "deep" and self.license_info and self.license_info.tier == "free":
            console.print("[yellow]⚠ Deep Scan requires Premium. Using Quick Scan.[/yellow]")
            mode = "quick"
        
        from modules.domain_intel import DomainIntel
        
        scanner = DomainIntel(self.language)
        results = scanner.scan(domain, scan_mode=mode)
        
        # Log usage
        self._log_usage("domain", domain, mode)
        
        self._display_and_export(results, "domain_intel", LANG("menu_domain"))
    
    def _ip_scanner(self):
        """IP/Server scanner."""
        if not self._check_limit("ip"):
            return
        
        Banner.show_module_header(LANG("menu_ip"), "🖥️")
        
        ip = Prompt.ask(LANG("enter_ip"))
        if not ip:
            return
        
        console.print(f"\n[cyan]{LANG('scan_type')}:[/cyan]")
        console.print("[1] " + LANG("passive_scan"))
        console.print("[2] " + LANG("active_scan"))
        console.print("[3] " + LANG("both_scan"))
        
        scan_choice = Prompt.ask("Choice", choices=["1", "2", "3"], default="3")
        scan_type = {"1": "passive", "2": "active", "3": "both"}[scan_choice]
        
        from modules.ip_scanner import IPScanner
        
        scanner = IPScanner(self.language)
        results = scanner.scan(ip, scan_type=scan_type)
        
        # Log usage
        self._log_usage("ip", ip, scan_type)
        
        self._display_and_export(results, "ip_scanner", LANG("menu_ip"))
    
    def _person_osint(self):
        """Person OSINT."""
        if not self._check_limit("person"):
            return
        
        Banner.show_module_header(LANG("menu_person"), "🔎")
        
        name = Prompt.ask(LANG("enter_name"))
        if not name:
            return
        
        location = Prompt.ask("Location (optional)", default="")
        
        from modules.person_osint import PersonOSINT
        
        scanner = PersonOSINT(self.language)
        results = scanner.scan(name, location=location)
        
        # Log usage
        self._log_usage("person", name)
        
        console.print("\n[cyan]Possible usernames:[/cyan]")
        for un in results.get("possible_usernames", [])[:10]:
            console.print(f"  • {un}")
        
        self._display_and_export(results, "person_osint", LANG("menu_person"))
    
    def _image_osint(self):
        """Image OSINT."""
        if not self._check_limit("image"):
            return
        
        Banner.show_module_header(LANG("menu_image"), "🖼️")
        
        path = Prompt.ask(LANG("enter_image_path"))
        if not path:
            return
        
        from modules.image_osint import ImageOSINT
        
        scanner = ImageOSINT(self.language)
        results = scanner.scan(path)
        
        # Log usage
        self._log_usage("image", path)
        
        geo = results.get("geolocation")
        if geo:
            console.print(f"\n[yellow]📍 GPS Found: {geo.get('coordinates')}[/yellow]")
            console.print(f"   Google Maps: {geo.get('google_maps')}")
        
        self._display_and_export(results, "image_osint", LANG("menu_image"))
    
    def _social_deep(self):
        """Social media deep scan."""
        if not self._check_limit("social"):
            return
        
        Banner.show_module_header(LANG("menu_social"), "📱")
        
        url = Prompt.ask(LANG("enter_social_url"))
        if not url:
            return
        
        from modules.social_deep import SocialDeepScan
        
        scanner = SocialDeepScan(self.language)
        results = scanner.scan(url)
        
        # Log usage
        self._log_usage("social", url)
        
        self._display_and_export(results, "social_deep", LANG("menu_social"))
    
    def _geolocation(self):
        """Geolocation OSINT."""
        if not self._check_limit("geo"):
            return
        
        Banner.show_module_header(LANG("menu_geolocation"), "📍")
        
        location = Prompt.ask(LANG("enter_coordinates"))
        if not location:
            return
        
        from modules.geolocation import GeolocationOSINT
        
        scanner = GeolocationOSINT(self.language)
        results = scanner.scan(location)
        
        # Log usage
        self._log_usage("geo", location)
        
        maps = results.get("maps", {})
        if maps:
            console.print("\n[cyan]Map Links:[/cyan]")
            for name, url in list(maps.items())[:3]:
                console.print(f"  • {name}: {url}")
        
        self._display_and_export(results, "geolocation", LANG("menu_geolocation"))
    
    def _display_and_export(self, results: dict, prefix: str, title: str):
        """Display results and prompt for export."""
        console.print()
        
        console.print(f"\n[cyan]{LANG('select_output')}:[/cyan]")
        console.print("[1] " + LANG("output_display"))
        console.print("[2] " + LANG("output_json"))
        console.print("[3] " + LANG("output_txt"))
        console.print("[4] " + LANG("output_html"))
        console.print("[5] " + LANG("output_all"))
        console.print("[6] Export PDF")
        
        choice = Prompt.ask("Choice", choices=["1", "2", "3", "4", "5", "6"], default="1")
        
        if choice == "1":
            self.output_manager.display_console(results, title)
        elif choice == "2":
            self.output_manager.display_console(results, title)
            self.output_manager.export_json(results, prefix=prefix)
        elif choice == "3":
            self.output_manager.display_console(results, title)
            self.output_manager.export_txt(results, prefix=prefix)
        elif choice == "4":
            self.output_manager.display_console(results, title)
            self.output_manager.export_html(results, prefix=prefix, title=title)
        elif choice == "5":
            self.output_manager.display_console(results, title)
            self.output_manager.export_all(results, prefix=prefix, title=title)
        elif choice == "6":
            self.output_manager.display_console(results, title)
            from core.pdf_export import generate_pdf_report
            pdf_path = generate_pdf_report(results, title)
            console.print(f"\n[green]PDF saved: {pdf_path}[/green]")
    
    def _exit(self):
        """Exit application."""
        console.print(f"\n[cyan]{LANG('goodbye')}[/cyan]")
        console.print(f"[dim]By {config.AUTHOR} | v{config.VERSION}[/dim]\n")


def main():
    """Main entry point."""
    app = CKSearch()
    app.run()


if __name__ == "__main__":
    main()
