"""
CKSEARCH - Admin Manager Tool
==============================
Script untuk mengelola backend CKSEARCH (Generate License, Stats, dll)
"""
import requests
import sys
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

# Ganti dengan URL backend Anda jika sudah online
API_BASE_URL = "https://api.cimeng.web.id" 
ADMIN_SECRET = "cimenk-admin-2024-secret"  # Samakan dengan yang di Railway env vars

class AdminManager:
    def __init__(self):
        self.token = None
    
    def login(self):
        """Login ke admin panel untuk mendapatkan JWT token."""
        try:
            r = requests.post(f"{API_BASE_URL}/api/v1/admin/login", json={"secret": ADMIN_SECRET})
            if r.status_code == 200:
                self.token = r.json().get("access_token")
                return True
            return False
        except Exception as e:
            console.print(f"[red]Error Login: {e}[/red]")
            return False

    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def show_stats(self):
        """Menampilkan statistik sistem."""
        try:
            r = requests.get(f"{API_BASE_URL}/api/v1/admin/stats", headers=self.get_headers())
            if r.status_code == 200:
                data = r.json()
                table = Table(title="📊 System Statistics")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="white")
                
                table.add_row("Total Users", str(data.get("total_users")))
                table.add_row("Premium Users", str(data.get("premium_users")))
                table.add_row("Total Requests", str(data.get("total_requests")))
                table.add_row("Active Licenses", str(data.get("active_licenses")))
                
                console.print(table)
            else:
                console.print(f"[red]Gagal mengambil data: {r.text}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def generate_license(self):
        """Generate license key baru."""
        duration = Prompt.ask("Durasi (hari)", choices=["7", "14", "30", "365"], default="30")
        note = Prompt.ask("Catatan (opsional)", default="Customer")
        
        try:
            r = requests.post(
                f"{API_BASE_URL}/api/v1/admin/license/generate",
                headers=self.get_headers(),
                json={"duration_days": int(duration), "note": note}
            )
            if r.status_code == 200:
                key = r.json().get("key")
                console.print(Panel(f"Berhasil membuat license key!\n\n[bold green]{key}[/bold green]\n\nDurasi: {duration} Hari", title="Success"))
            else:
                console.print(f"[red]Gagal: {r.text}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def list_users(self):
        """List pengguna terdaftar."""
        try:
            r = requests.get(f"{API_BASE_URL}/api/v1/admin/users", headers=self.get_headers())
            if r.status_code == 200:
                users = r.json()
                table = Table(title="👥 User List")
                table.add_column("Fingerprint", style="dim")
                table.add_column("Tier", style="bold")
                table.add_column("Total Req", justify="right")
                table.add_row(*["---", "---", "---"])
                
                for u in users[:10]: # Limit 10 for display
                    tier_style = "green" if u['tier'] == "premium" else "white"
                    table.add_row(u['fingerprint'][:15] + "...", f"[{tier_style}]{u['tier']}[/ ]", str(u['total_requests']))
                
                console.print(table)
            else:
                console.print(f"[red]Gagal: {r.text}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

def main():
    manager = AdminManager()
    console.print("[cyan]CKSEARCH ADMIN MANAGER[/cyan]")
    
    if not manager.login():
        console.print("[red]Gagal login. Pastikan API_BASE_URL dan ADMIN_SECRET benar.[/red]")
        return

    while True:
        console.print("\n[bold]Menu Admin:[/bold]")
        console.print("[1] Statistik Sistem")
        console.print("[2] Buat License Key (Premium)")
        console.print("[3] Daftar Pengguna")
        console.print("[0] Keluar")
        
        choice = Prompt.ask("Pilih", choices=["0", "1", "2", "3"])
        
        if choice == "1":
            manager.show_stats()
        elif choice == "2":
            manager.generate_license()
        elif choice == "3":
            manager.list_users()
        elif choice == "0":
            break

if __name__ == "__main__":
    main()
