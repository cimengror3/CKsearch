"""
CKSEARCH - PDF Report Generator
=================================
Generate professional PDF reports from scan results.
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional

import config


def generate_pdf_report(
    results: Dict[str, Any],
    title: str,
    output_path: Optional[str] = None,
) -> str:
    """
    Generate PDF report from scan results.
    
    Args:
        results: Scan results dictionary
        title: Report title
        output_path: Optional output path (default: results/report_timestamp.pdf)
    
    Returns:
        Path to generated PDF file
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm, mm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak, Image, HRFlowable
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        # Fallback if reportlab not installed
        return _generate_simple_report(results, title, output_path)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not output_path:
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(config.OUTPUT_DIR, f"report_{timestamp}.pdf")
    
    # Create document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a1a2e'),
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.HexColor('#16213e'),
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
    )
    
    # Build content
    content = []
    
    # Header
    content.append(Paragraph(f"CKSEARCH Report", title_style))
    content.append(Paragraph(f"<b>{title}</b>", styles['Heading3']))
    content.append(Spacer(1, 10))
    
    # Metadata table
    metadata = results.get("metadata", {})
    meta_data = [
        ["Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB")],
        ["Version", config.VERSION],
        ["Scan Mode", results.get("scan_mode", "N/A")],
        ["Duration", f"{metadata.get('duration', 0):.2f} seconds"],
    ]
    
    meta_table = Table(meta_data, colWidths=[4*cm, 8*cm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    content.append(meta_table)
    content.append(Spacer(1, 20))
    
    # Horizontal line
    content.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    content.append(Spacer(1, 20))
    
    # Results section
    content.append(Paragraph("Scan Results", heading_style))
    
    # Format results as table
    result_data = _flatten_dict(results, exclude=["metadata"])
    
    for section, data in result_data.items():
        if not data:
            continue
            
        content.append(Paragraph(f"<b>{section.replace('_', ' ').title()}</b>", styles['Heading4']))
        
        if isinstance(data, dict):
            table_data = [[str(k), str(v)[:80]] for k, v in data.items() if v]
            if table_data:
                t = Table(table_data, colWidths=[4*cm, 10*cm])
                t.setStyle(TableStyle([
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f8f8')),
                ]))
                content.append(t)
        elif isinstance(data, list):
            for item in data[:20]:  # Limit to 20 items
                if isinstance(item, dict):
                    text = " | ".join(f"{k}: {v}" for k, v in item.items() if v)
                else:
                    text = str(item)
                content.append(Paragraph(f"• {text[:100]}", normal_style))
        else:
            content.append(Paragraph(str(data)[:200], normal_style))
        
        content.append(Spacer(1, 10))
    
    # Footer
    content.append(Spacer(1, 30))
    content.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    content.append(Spacer(1, 10))
    content.append(Paragraph(
        f"Generated by CKSEARCH v{config.VERSION} | {config.AUTHOR}",
        ParagraphStyle('Footer', fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))
    content.append(Paragraph(
        "This report is confidential. Handle with care.",
        ParagraphStyle('Footer', fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    # Build PDF
    doc.build(content)
    
    return output_path


def _flatten_dict(d: Dict, parent_key: str = '', exclude: list = None) -> Dict:
    """Flatten nested dictionary for display."""
    if exclude is None:
        exclude = []
    
    result = {}
    for key, value in d.items():
        if key in exclude:
            continue
        
        new_key = f"{parent_key}.{key}" if parent_key else key
        
        if isinstance(value, dict) and len(value) < 10:
            # Keep as dict for small dictionaries
            result[new_key] = value
        elif isinstance(value, list):
            result[new_key] = value
        else:
            result[new_key] = value
    
    return result


def _generate_simple_report(results: Dict, title: str, output_path: Optional[str]) -> str:
    """Generate simple text report if reportlab not available."""
    import json
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not output_path:
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(config.OUTPUT_DIR, f"report_{timestamp}.txt")
    
    with open(output_path, "w") as f:
        f.write(f"CKSEARCH Report\n")
        f.write(f"{'='*50}\n\n")
        f.write(f"Title: {title}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Version: {config.VERSION}\n\n")
        f.write(f"{'='*50}\n\n")
        f.write("Results:\n\n")
        f.write(json.dumps(results, indent=2, default=str))
    
    return output_path


if __name__ == "__main__":
    # Test PDF generation
    test_results = {
        "target": "test@example.com",
        "scan_mode": "deep",
        "valid": True,
        "domain_info": {
            "domain": "example.com",
            "provider": "Custom",
        },
        "breaches": {
            "found": True,
            "count": 3,
            "details": [
                {"name": "Breach 1"},
                {"name": "Breach 2"},
            ]
        },
        "metadata": {
            "duration": 5.23,
        }
    }
    
    path = generate_pdf_report(test_results, "Email OSINT - test@example.com")
    print(f"Report generated: {path}")
