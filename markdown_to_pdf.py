
#!/usr/bin/env python3
"""
Convert EIP_Sentiment_Analyzer_Chapter.md to PDF
"""

import os
import re
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

def convert_markdown_to_pdf():
    """Convert the markdown chapter to PDF"""
    
    # Read the markdown file
    with open('EIP_Sentiment_Analyzer_Chapter.md', 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Create PDF document
    doc = SimpleDocTemplate("EIP_Sentiment_Analyzer_Chapter.pdf", pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.darkblue,
        alignment=TA_CENTER
    )
    
    heading1_style = ParagraphStyle(
        'Heading1',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        spaceBefore=30,
        textColor=colors.darkgreen
    )
    
    heading2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=15,
        spaceBefore=20,
        textColor=colors.darkblue
    )
    
    heading3_style = ParagraphStyle(
        'Heading3',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=15,
        textColor=colors.black
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Courier',
        backColor=colors.lightgrey,
        leftIndent=20,
        rightIndent=20,
        spaceAfter=10,
        spaceBefore=10
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        leading=14
    )
    
    # Split content into lines
    lines = markdown_content.split('\n')
    
    in_code_block = False
    code_content = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines (but add small spacer)
        if not line:
            if not in_code_block:
                story.append(Spacer(1, 6))
            continue
        
        # Handle code blocks
        if line.startswith('```'):
            if in_code_block:
                # End of code block
                if code_content:
                    code_text = '\n'.join(code_content)
                    # Clean up code text for reportlab
                    code_text = code_text.replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(code_text, code_style))
                code_content = []
                in_code_block = False
            else:
                # Start of code block
                in_code_block = True
            continue
        
        if in_code_block:
            code_content.append(line)
            continue
        
        # Handle headers
        if line.startswith('# '):
            # Main title
            title_text = line[2:].strip()
            story.append(Paragraph(title_text, title_style))
            story.append(Spacer(1, 20))
        elif line.startswith('## '):
            # H2 headers
            header_text = line[3:].strip()
            story.append(Paragraph(header_text, heading1_style))
        elif line.startswith('### '):
            # H3 headers
            header_text = line[4:].strip()
            story.append(Paragraph(header_text, heading2_style))
        elif line.startswith('#### '):
            # H4 headers
            header_text = line[5:].strip()
            story.append(Paragraph(header_text, heading3_style))
        elif line.startswith('- ') or line.startswith('* '):
            # Bullet points
            bullet_text = line[2:].strip()
            bullet_text = process_markdown_text(bullet_text)
            story.append(Paragraph(f"• {bullet_text}", body_style))
        elif re.match(r'^\d+\.', line):
            # Numbered lists
            list_text = re.sub(r'^\d+\.\s*', '', line)
            list_text = process_markdown_text(list_text)
            story.append(Paragraph(list_text, body_style))
        else:
            # Regular paragraphs
            if line and not line.startswith('#'):
                paragraph_text = process_markdown_text(line)
                story.append(Paragraph(paragraph_text, body_style))
    
    # Build the PDF
    doc.build(story)
    return "EIP_Sentiment_Analyzer_Chapter.pdf"

def process_markdown_text(text):
    """Process markdown formatting in text"""
    # First escape any existing HTML characters in the content
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Handle bold text
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Handle italic text  
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Handle inline code - use simpler approach to avoid HTML attribute issues
    text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
    # Handle links (simple conversion)
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', text)
    
    return text

if __name__ == "__main__":
    try:
        pdf_file = convert_markdown_to_pdf()
        print(f"✅ PDF created successfully: {pdf_file}")
        print(f"📄 File size: {os.path.getsize(pdf_file) / 1024:.1f} KB")
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
