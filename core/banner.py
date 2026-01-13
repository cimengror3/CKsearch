"""
CKSEARCH - Banner Module
=========================
ASCII art logo dan disclaimer display.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
import pyfiglet
import config

console = Console()


class Banner:
    """Class untuk menampilkan banner dan disclaimer."""
    
    LOGO_COLOR = "cyan"
    AUTHOR_COLOR = "yellow"
    VERSION_COLOR = "green"
    DISCLAIMER_COLOR = "red"
    
    @staticmethod
    def get_ascii_logo() -> str:
        """Generate ASCII art logo."""
        # Menggunakan font yang bagus untuk logo
        ascii_art = pyfiglet.figlet_format("CKSEARCH", font="slant")
        return ascii_art
    
    @classmethod
    def show(cls, language: str = "id") -> None:
        """
        Tampilkan banner lengkap dengan logo, author, dan disclaimer.
        
        Args:
            language: Bahasa untuk disclaimer ("id" atau "en")
        """
        console.clear()
        
        # ASCII Logo
        logo = cls.get_ascii_logo()
        console.print(logo, style=f"bold {cls.LOGO_COLOR}")
        
        # Author & Version
        author_text = Text()
        author_text.append("By : ", style="white")
        author_text.append(config.AUTHOR, style=f"bold {cls.AUTHOR_COLOR}")
        author_text.append("  |  ", style="dim")
        author_text.append(f"v{config.VERSION}", style=f"bold {cls.VERSION_COLOR}")
        console.print(author_text, justify="center")
        console.print()
        
        # Disclaimer
        if language == "id":
            disclaimer = cls._get_disclaimer_id()
        else:
            disclaimer = cls._get_disclaimer_en()
        
        panel = Panel(
            disclaimer,
            title="⚠️  DISCLAIMER  ⚠️",
            title_align="center",
            border_style=cls.DISCLAIMER_COLOR,
            box=box.DOUBLE_EDGE,
            padding=(1, 2),
        )
        console.print(panel)
        console.print()
    
    @staticmethod
    def _get_disclaimer_id() -> Text:
        """Disclaimer dalam Bahasa Indonesia."""
        text = Text()
        text.append("PERINGATAN PENTING!\n\n", style="bold red")
        text.append("Tools ini dibuat untuk tujuan ")
        text.append("EDUKASI", style="bold yellow")
        text.append(" dan ")
        text.append("INVESTIGASI LEGAL", style="bold yellow")
        text.append(" saja.\n\n")
        
        text.append("• ", style="red")
        text.append("Penggunaan untuk kegiatan ilegal adalah TERLARANG\n")
        text.append("• ", style="red")
        text.append("Pengguna bertanggung jawab penuh atas tindakannya\n")
        text.append("• ", style="red")
        text.append("Hormati privasi dan hukum yang berlaku\n")
        text.append("• ", style="red")
        text.append("Developer tidak bertanggung jawab atas penyalahgunaan\n\n")
        
        text.append("Dengan menggunakan tools ini, Anda ", style="dim")
        text.append("SETUJU", style="bold green")
        text.append(" dengan ketentuan di atas.", style="dim")
        
        return text
    
    @staticmethod
    def _get_disclaimer_en() -> Text:
        """Disclaimer in English."""
        text = Text()
        text.append("IMPORTANT WARNING!\n\n", style="bold red")
        text.append("This tool is intended for ")
        text.append("EDUCATIONAL", style="bold yellow")
        text.append(" and ")
        text.append("LEGAL INVESTIGATION", style="bold yellow")
        text.append(" purposes only.\n\n")
        
        text.append("• ", style="red")
        text.append("Illegal use is PROHIBITED\n")
        text.append("• ", style="red")
        text.append("Users are fully responsible for their actions\n")
        text.append("• ", style="red")
        text.append("Respect privacy and applicable laws\n")
        text.append("• ", style="red")
        text.append("Developer is not responsible for any misuse\n\n")
        
        text.append("By using this tool, you ", style="dim")
        text.append("AGREE", style="bold green")
        text.append(" to the terms above.", style="dim")
        
        return text
    
    @classmethod
    def show_module_header(cls, module_name: str, icon: str = "🔍") -> None:
        """
        Tampilkan header untuk modul tertentu.
        
        Args:
            module_name: Nama modul
            icon: Emoji icon
        """
        console.print()
        console.rule(f"{icon} {module_name}", style="cyan")
        console.print()
    
    @classmethod
    def show_result_header(cls, title: str) -> None:
        """Tampilkan header untuk hasil."""
        console.print()
        panel = Panel(
            title,
            style="bold green",
            box=box.ROUNDED,
        )
        console.print(panel)


# Quick access function
def show_banner(language: str = "id") -> None:
    """Shortcut untuk menampilkan banner."""
    Banner.show(language)


if __name__ == "__main__":
    # Test banner
    Banner.show("id")
    input("\nTekan Enter untuk lihat versi English...")
    Banner.show("en")
