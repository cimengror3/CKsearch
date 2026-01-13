"""
CKSEARCH - Base Scanner Module
===============================
Base class untuk semua scanner/modules.
"""

import time
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

import config

console = Console()


class BaseScanner(ABC):
    """Base class untuk semua OSINT scanner."""
    
    def __init__(self, name: str, language: str = "id"):
        """
        Initialize scanner.
        
        Args:
            name: Scanner name
            language: Language code
        """
        self.name = name
        self.language = language
        self.start_time = None
        self.end_time = None
        self.results = {}
        self.errors = []
        self.warnings = []
    
    @abstractmethod
    def scan(self, target: str, **options) -> Dict[str, Any]:
        """
        Perform scan on target.
        
        Args:
            target: Target to scan
            **options: Additional options
            
        Returns:
            Scan results dictionary
        """
        pass
    
    async def async_scan(self, target: str, **options) -> Dict[str, Any]:
        """
        Async version of scan.
        Override this for async scanning capability.
        """
        return self.scan(target, **options)
    
    def _start(self) -> None:
        """Mark scan start time."""
        self.start_time = datetime.now()
        self.results = {}
        self.errors = []
        self.warnings = []
    
    def _finish(self) -> None:
        """Mark scan end time."""
        self.end_time = datetime.now()
    
    def _get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def _add_error(self, error: str) -> None:
        """Add error message."""
        self.errors.append(error)
        console.print(f"[red]✗ Error: {error}[/red]")
    
    def _add_warning(self, warning: str) -> None:
        """Add warning message."""
        self.warnings.append(warning)
        console.print(f"[yellow]⚠ Warning: {warning}[/yellow]")
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get scan metadata."""
        return {
            "scanner": self.name,
            "timestamp": self.start_time.isoformat() if self.start_time else None,
            "elapsed_seconds": self._get_elapsed_time(),
            "errors": self.errors,
            "warnings": self.warnings,
        }
    
    @staticmethod
    def show_progress(description: str, total: int = None):
        """Create progress context manager."""
        if total:
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            )
        else:
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            )
    
    @staticmethod
    def create_progress_bar():
        """Create and return a rich progress bar."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TextColumn("[dim]{task.fields[status]}"),
            console=console,
        )


class AsyncScanner(BaseScanner):
    """Base class untuk async scanners."""
    
    def __init__(self, name: str, language: str = "id", max_concurrent: int = None):
        super().__init__(name, language)
        self.max_concurrent = max_concurrent or config.MAX_CONCURRENT_REQUESTS
        self.semaphore = None
    
    async def _init_semaphore(self):
        """Initialize semaphore for concurrency control."""
        if self.semaphore is None:
            self.semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def _run_with_semaphore(self, coro):
        """Run coroutine with semaphore."""
        await self._init_semaphore()
        async with self.semaphore:
            return await coro
    
    async def run_batch(self, tasks: List[Any]) -> List[Any]:
        """
        Run batch of async tasks with concurrency limit.
        
        Args:
            tasks: List of coroutines
            
        Returns:
            List of results
        """
        await self._init_semaphore()
        
        async def wrapped(task):
            async with self.semaphore:
                return await task
        
        return await asyncio.gather(*[wrapped(t) for t in tasks], return_exceptions=True)
    
    def scan(self, target: str, **options) -> Dict[str, Any]:
        """Sync wrapper for async scan."""
        return asyncio.run(self.async_scan(target, **options))


class PortScanner:
    """Port scanner helper class."""
    
    def __init__(self, timeout: float = 2.0):
        self.timeout = timeout
    
    async def check_port(self, host: str, port: int) -> Dict[str, Any]:
        """
        Check if port is open.
        
        Args:
            host: Target host
            port: Port number
            
        Returns:
            Port status dictionary
        """
        try:
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=self.timeout)
            
            # Try to get banner
            banner = ""
            try:
                writer.write(b"\r\n")
                await writer.drain()
                data = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                banner = data.decode("utf-8", errors="ignore").strip()
            except:
                pass
            
            writer.close()
            await writer.wait_closed()
            
            return {
                "port": port,
                "state": "open",
                "service": self._guess_service(port),
                "banner": banner[:200] if banner else None,
            }
            
        except asyncio.TimeoutError:
            return {"port": port, "state": "filtered", "service": self._guess_service(port)}
        except ConnectionRefusedError:
            return {"port": port, "state": "closed", "service": self._guess_service(port)}
        except Exception:
            return {"port": port, "state": "unknown", "service": self._guess_service(port)}
    
    async def scan_ports(self, host: str, ports: List[int] = None) -> List[Dict[str, Any]]:
        """
        Scan multiple ports.
        
        Args:
            host: Target host
            ports: List of ports to scan
            
        Returns:
            List of port results
        """
        if ports is None:
            ports = config.COMMON_PORTS
        
        tasks = [self.check_port(host, port) for port in ports]
        results = await asyncio.gather(*tasks)
        
        # Filter only open/filtered ports
        return [r for r in results if r["state"] in ["open", "filtered"]]
    
    @staticmethod
    def _guess_service(port: int) -> str:
        """Guess service name from port number."""
        services = {
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            111: "RPC",
            135: "MSRPC",
            139: "NetBIOS",
            143: "IMAP",
            443: "HTTPS",
            445: "SMB",
            993: "IMAPS",
            995: "POP3S",
            1433: "MSSQL",
            1521: "Oracle",
            1723: "PPTP",
            3306: "MySQL",
            3389: "RDP",
            5432: "PostgreSQL",
            5900: "VNC",
            6379: "Redis",
            8080: "HTTP-Proxy",
            8443: "HTTPS-Alt",
            27017: "MongoDB",
        }
        return services.get(port, "unknown")
