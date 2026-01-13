"""
CKSEARCH - Output Module
=========================
Output manager untuk berbagai format export.
"""

import json
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import box
from jinja2 import Template

import config

console = Console()


class OutputManager:
    """Manager untuk handling berbagai format output."""
    
    def __init__(self, language: str = "id"):
        """
        Initialize output manager.
        
        Args:
            language: Language code for labels
        """
        self.language = language
        self.output_dir = config.OUTPUT_DIR
        
    def generate_filename(self, prefix: str, extension: str) -> Path:
        """
        Generate unique filename dengan timestamp.
        
        Args:
            prefix: File prefix
            extension: File extension
            
        Returns:
            Full path to file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.{extension}"
        return self.output_dir / filename
    
    def display_console(self, data: Dict[str, Any], title: str = "Results") -> None:
        """
        Display hasil di console dengan formatting rich.
        
        Args:
            data: Data untuk ditampilkan
            title: Judul
        """
        console.print()
        panel = Panel(
            self._dict_to_tree(data),
            title=f"📊 {title}",
            border_style="green",
            box=box.DOUBLE,
        )
        console.print(panel)
    
    def display_table(
        self,
        data: List[Dict[str, Any]],
        columns: List[str],
        title: str = "Results"
    ) -> None:
        """
        Display data sebagai table.
        
        Args:
            data: List of dictionaries
            columns: Column names to show
            title: Table title
        """
        table = Table(title=title, box=box.ROUNDED, show_lines=True)
        
        # Add columns
        for col in columns:
            table.add_column(col.title(), style="cyan", overflow="fold")
        
        # Add rows
        for row in data:
            values = [str(row.get(col, "N/A")) for col in columns]
            table.add_row(*values)
        
        console.print(table)
    
    def _dict_to_tree(self, data: Dict[str, Any], tree: Tree = None) -> Tree:
        """Convert dictionary to rich Tree."""
        if tree is None:
            tree = Tree("📁 Data")
        
        for key, value in data.items():
            if isinstance(value, dict):
                branch = tree.add(f"[cyan]{key}[/cyan]")
                self._dict_to_tree(value, branch)
            elif isinstance(value, list):
                branch = tree.add(f"[cyan]{key}[/cyan] ({len(value)} items)")
                for i, item in enumerate(value[:10]):  # Limit to 10 items
                    if isinstance(item, dict):
                        sub_branch = branch.add(f"[yellow]Item {i+1}[/yellow]")
                        self._dict_to_tree(item, sub_branch)
                    else:
                        branch.add(f"[green]{item}[/green]")
                if len(value) > 10:
                    branch.add(f"[dim]... and {len(value) - 10} more[/dim]")
            else:
                if value is None:
                    tree.add(f"[cyan]{key}:[/cyan] [dim]N/A[/dim]")
                elif value is True:
                    tree.add(f"[cyan]{key}:[/cyan] [green]✓ Yes[/green]")
                elif value is False:
                    tree.add(f"[cyan]{key}:[/cyan] [red]✗ No[/red]")
                else:
                    tree.add(f"[cyan]{key}:[/cyan] [white]{value}[/white]")
        
        return tree
    
    def export_json(
        self,
        data: Dict[str, Any],
        filename: str = None,
        prefix: str = "result"
    ) -> str:
        """
        Export data ke JSON file.
        
        Args:
            data: Data untuk export
            filename: Optional custom filename
            prefix: Filename prefix
            
        Returns:
            Path to saved file
        """
        if filename:
            filepath = self.output_dir / filename
        else:
            filepath = self.generate_filename(prefix, "json")
        
        # Add metadata
        export_data = {
            "metadata": {
                "tool": config.PROJECT_NAME,
                "version": config.VERSION,
                "exported_at": datetime.now().isoformat(),
            },
            "data": data,
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        console.print(f"[green]✓ JSON saved:[/green] {filepath}")
        return str(filepath)
    
    def export_txt(
        self,
        data: Dict[str, Any],
        filename: str = None,
        prefix: str = "result"
    ) -> str:
        """
        Export data ke TXT/Markdown file.
        
        Args:
            data: Data untuk export
            filename: Optional custom filename
            prefix: Filename prefix
            
        Returns:
            Path to saved file
        """
        if filename:
            filepath = self.output_dir / filename
        else:
            filepath = self.generate_filename(prefix, "md")
        
        content = self._dict_to_markdown(data)
        
        # Add header
        header = f"""# {config.PROJECT_NAME} Report
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Version:** {config.VERSION}

---

"""
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(header + content)
        
        console.print(f"[green]✓ TXT/MD saved:[/green] {filepath}")
        return str(filepath)
    
    def _dict_to_markdown(self, data: Dict[str, Any], level: int = 2) -> str:
        """Convert dictionary to Markdown format."""
        lines = []
        
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{'#' * level} {key.replace('_', ' ').title()}\n")
                lines.append(self._dict_to_markdown(value, level + 1))
            elif isinstance(value, list):
                lines.append(f"{'#' * level} {key.replace('_', ' ').title()}\n")
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            lines.append(f"- **{k}:** {v}")
                        lines.append("")
                    else:
                        lines.append(f"- {item}")
                lines.append("")
            else:
                display_value = "✓ Yes" if value is True else "✗ No" if value is False else value or "N/A"
                lines.append(f"- **{key.replace('_', ' ').title()}:** {display_value}")
        
        return "\n".join(lines)
    
    def export_csv(
        self,
        data: List[Dict[str, Any]],
        filename: str = None,
        prefix: str = "result"
    ) -> str:
        """
        Export data ke CSV file.
        
        Args:
            data: List of dictionaries
            filename: Optional custom filename
            prefix: Filename prefix
            
        Returns:
            Path to saved file
        """
        if filename:
            filepath = self.output_dir / filename
        else:
            filepath = self.generate_filename(prefix, "csv")
        
        if not data:
            console.print("[yellow]No data to export[/yellow]")
            return ""
        
        # Flatten nested dicts
        flat_data = [self._flatten_dict(item) for item in data]
        
        # Get all keys
        all_keys = set()
        for item in flat_data:
            all_keys.update(item.keys())
        
        fieldnames = sorted(all_keys)
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flat_data)
        
        console.print(f"[green]✓ CSV saved:[/green] {filepath}")
        return str(filepath)
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = "", sep: str = "_") -> Dict[str, Any]:
        """Flatten nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            elif isinstance(v, list):
                items.append((new_key, ", ".join(str(x) for x in v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def export_html(
        self,
        data: Dict[str, Any],
        filename: str = None,
        prefix: str = "result",
        title: str = "OSINT Report"
    ) -> str:
        """
        Export data ke HTML report.
        
        Args:
            data: Data untuk export
            filename: Optional custom filename
            prefix: Filename prefix
            title: Report title
            
        Returns:
            Path to saved file
        """
        if filename:
            filepath = self.output_dir / filename
        else:
            filepath = self.generate_filename(prefix, "html")
        
        html_content = self._generate_html_report(data, title)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        console.print(f"[green]✓ HTML saved:[/green] {filepath}")
        return str(filepath)
    
    def _generate_html_report(self, data: Dict[str, Any], title: str) -> str:
        """Generate professional HTML report."""
        template = Template("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - {{ project_name }}</title>
    <style>
        :root {
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --accent-green: #3fb950;
            --accent-blue: #58a6ff;
            --accent-purple: #a371f7;
            --accent-red: #f85149;
            --accent-yellow: #d29922;
            --border-color: #30363d;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            padding: 40px 20px;
            background: linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary));
            border-radius: 16px;
            margin-bottom: 30px;
            border: 1px solid var(--border-color);
        }
        
        .logo {
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
        }
        
        .meta {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        .meta-item {
            background: var(--bg-primary);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        
        .section {
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid var(--border-color);
        }
        
        .section-title {
            font-size: 1.5rem;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--accent-blue);
        }
        
        .section-title::before {
            content: '';
            width: 4px;
            height: 24px;
            background: var(--accent-blue);
            border-radius: 2px;
        }
        
        .data-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
        }
        
        .data-card {
            background: var(--bg-tertiary);
            padding: 16px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        
        .data-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .data-value {
            font-size: 1.1rem;
            font-weight: 600;
            word-break: break-word;
        }
        
        .data-value.success {
            color: var(--accent-green);
        }
        
        .data-value.warning {
            color: var(--accent-yellow);
        }
        
        .data-value.danger {
            color: var(--accent-red);
        }
        
        .list-section {
            margin-top: 16px;
        }
        
        .list-item {
            background: var(--bg-tertiary);
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 8px;
            border-left: 3px solid var(--accent-purple);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .list-item a {
            color: var(--accent-blue);
            text-decoration: none;
        }
        
        .list-item a:hover {
            text-decoration: underline;
        }
        
        .badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .badge.found {
            background: rgba(63, 185, 80, 0.2);
            color: var(--accent-green);
        }
        
        .badge.not-found {
            background: rgba(139, 148, 158, 0.2);
            color: var(--text-secondary);
        }
        
        .stats-row {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .stat-box {
            flex: 1;
            min-width: 150px;
            background: var(--bg-tertiary);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid var(--border-color);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--accent-blue);
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-top: 4px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        
        th {
            background: var(--bg-tertiary);
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85rem;
        }
        
        tr:hover {
            background: var(--bg-tertiary);
        }
        
        footer {
            text-align: center;
            padding: 30px;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        footer a {
            color: var(--accent-blue);
            text-decoration: none;
        }
        
        @media print {
            body {
                background: white;
                color: black;
            }
            
            .section, header {
                border: 1px solid #ddd;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">{{ project_name }}</div>
            <div class="subtitle">{{ title }}</div>
            <div class="meta">
                <span class="meta-item">📅 {{ timestamp }}</span>
                <span class="meta-item">🔧 Version {{ version }}</span>
            </div>
        </header>
        
        {% for section_name, section_data in data.items() %}
        <section class="section">
            <h2 class="section-title">{{ section_name | replace('_', ' ') | title }}</h2>
            
            {% if section_data is mapping %}
                <div class="data-grid">
                {% for key, value in section_data.items() %}
                    <div class="data-card">
                        <div class="data-label">{{ key | replace('_', ' ') }}</div>
                        <div class="data-value {% if value == true %}success{% elif value == false %}danger{% endif %}">
                            {% if value == true %}✓ Yes
                            {% elif value == false %}✗ No
                            {% elif value is none %}N/A
                            {% else %}{{ value }}{% endif %}
                        </div>
                    </div>
                {% endfor %}
                </div>
            {% elif section_data is iterable and section_data is not string %}
                <div class="list-section">
                {% for item in section_data %}
                    {% if item is mapping %}
                        <div class="list-item">
                            {% for k, v in item.items() %}
                                <span><strong>{{ k }}:</strong> {{ v }}</span>
                            {% endfor %}
                        </div>
                    {% else %}
                        <div class="list-item">{{ item }}</div>
                    {% endif %}
                {% endfor %}
                </div>
            {% else %}
                <p>{{ section_data }}</p>
            {% endif %}
        </section>
        {% endfor %}
        
        <footer>
            <p>Generated by <a href="#">{{ project_name }}</a> | By {{ author }}</p>
            <p>For educational and legal investigation purposes only.</p>
        </footer>
    </div>
</body>
</html>""")
        
        return template.render(
            title=title,
            project_name=config.PROJECT_NAME,
            version=config.VERSION,
            author=config.AUTHOR,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data=data,
        )
    
    def export_all(
        self,
        data: Dict[str, Any],
        prefix: str = "result",
        title: str = "OSINT Report"
    ) -> Dict[str, str]:
        """
        Export ke semua format.
        
        Args:
            data: Data untuk export
            prefix: Filename prefix
            title: Report title
            
        Returns:
            Dictionary of format -> filepath
        """
        results = {}
        
        results["json"] = self.export_json(data, prefix=prefix)
        results["txt"] = self.export_txt(data, prefix=prefix)
        results["html"] = self.export_html(data, prefix=prefix, title=title)
        
        # CSV hanya untuk list data
        if isinstance(data, list):
            results["csv"] = self.export_csv(data, prefix=prefix)
        
        return results


# Utility functions
def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[blue]ℹ[/blue] {message}")
