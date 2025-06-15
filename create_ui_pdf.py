#!/usr/bin/env python3
"""
Generate a comprehensive PDF documentation of the EIP Sentiment Analyzer UI
"""

import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from PIL import Image as PILImage
import subprocess
import time

def take_screenshot(url, filename, wait_time=3):
    """Take screenshot of a URL"""
    try:
        cmd = [
            'chromium', '--headless', '--disable-gpu', '--no-sandbox', 
            '--disable-dev-shm-usage', '--window-size=1920,1080',
            f'--screenshot=screenshots/{filename}', url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        time.sleep(wait_time)  # Wait for page to load
        return f'screenshots/{filename}'
    except Exception as e:
        print(f"Error taking screenshot for {url}: {e}")
        return None

def create_pdf_documentation():
    """Create comprehensive PDF documentation"""
    
    # Ensure screenshots directory exists
    os.makedirs('screenshots', exist_ok=True)
    
    # Define pages to capture
    pages = [
        {
            'name': 'Homepage',
            'url': 'http://localhost:5000/',
            'filename': 'home.png',
            'description': 'Main landing page showing public features (Smart Contract Generator, Dashboard) and admin login option'
        },
        {
            'name': 'Smart Contract Generator',
            'url': 'http://localhost:5000/smart-contract',
            'filename': 'smart_contracts.png',
            'description': 'AI-powered smart contract generation and analysis with EIP recommendations and sentiment warnings'
        },
        {
            'name': 'Dashboard',
            'url': 'http://localhost:5000/dashboard',
            'filename': 'dashboard.png',
            'description': 'Interactive visualizations of EIP sentiment analysis data with charts and filters'
        },
        {
            'name': 'Admin Login',
            'url': 'http://localhost:5000/login',
            'filename': 'login.png',
            'description': 'Authentication page for administrators to access CSV upload and results features'
        }
    ]
    
    # Create PDF document
    doc = SimpleDocTemplate("UI_Documentation.pdf", pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.darkgreen
    )
    
    # Title page
    story.append(Paragraph("EIP Sentiment Analyzer", title_style))
    story.append(Paragraph("User Interface Documentation", styles['Heading2']))
    story.append(Spacer(1, 20))
    
    # Project overview
    story.append(Paragraph("Project Overview", heading_style))
    overview_text = """
    The EIP Sentiment Analyzer is a Flask web application for advanced smart contract analysis 
    and EIP (Ethereum Improvement Proposal) evaluation, leveraging AI-powered insights and sentiment analysis.
    
    <b>Core Features:</b><br/>
    • Smart contract generation and analysis modes<br/>
    • AI-powered EIP recommendations with sentiment warnings<br/>
    • Sentiment-based code standard evaluations<br/>
    • Real-time blockchain data processing<br/>
    • Interactive dashboard with visualizations<br/>
    • Admin-controlled CSV upload and analysis pipeline
    """
    story.append(Paragraph(overview_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Access control information
    story.append(Paragraph("Access Control", heading_style))
    access_info = """
    <b>Public Access:</b><br/>
    • Homepage with feature overview<br/>
    • Smart Contract Generator (AI-powered analysis)<br/>
    • Dashboard with sentiment visualizations<br/>
    
    <b>Admin Access Only:</b><br/>
    • CSV file upload for sentiment analysis<br/>
    • Analysis results and job management<br/>
    • Detailed data exports and reports<br/>
    
    <b>Admin Credentials:</b><br/>
    • admin@example.com / admin123<br/>
    • admin@sentiment.com / password123
    """
    story.append(Paragraph(access_info, styles['Normal']))
    story.append(PageBreak())
    
    # Take screenshots and add to PDF
    for page in pages:
        print(f"Capturing {page['name']}...")
        
        # Take screenshot
        screenshot_path = take_screenshot(page['url'], page['filename'])
        
        # Add page heading
        story.append(Paragraph(page['name'], heading_style))
        story.append(Paragraph(f"<b>URL:</b> {page['url']}", styles['Normal']))
        story.append(Paragraph(f"<b>Description:</b> {page['description']}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Add screenshot if available
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                # Check image dimensions and resize if needed
                with PILImage.open(screenshot_path) as img:
                    width, height = img.size
                    # Scale to fit page width (with margins)
                    max_width = 7 * inch
                    max_height = 9 * inch
                    
                    scale = min(max_width / width, max_height / height)
                    new_width = width * scale
                    new_height = height * scale
                
                # Add image to PDF
                story.append(Image(screenshot_path, width=new_width, height=new_height))
                story.append(Spacer(1, 20))
                
            except Exception as e:
                story.append(Paragraph(f"Error loading screenshot: {e}", styles['Normal']))
                story.append(Spacer(1, 20))
        else:
            story.append(Paragraph("Screenshot not available", styles['Normal']))
            story.append(Spacer(1, 20))
        
        story.append(PageBreak())
    
    # Technical details page
    story.append(Paragraph("Technical Implementation", heading_style))
    tech_details = """
    <b>Technology Stack:</b><br/>
    • Flask web framework with Python backend<br/>
    • PostgreSQL database for data persistence<br/>
    • OpenAI GPT-4o for AI-powered analysis<br/>
    • Bootstrap dark theme for responsive UI<br/>
    • Chart.js for interactive visualizations<br/>
    • NLTK for sentiment analysis processing<br/>
    
    <b>Security Features:</b><br/>
    • Flask-Login for session management<br/>
    • Admin role-based access control<br/>
    • Secure file upload handling<br/>
    • Input validation and sanitization<br/>
    
    <b>Key Components:</b><br/>
    • Three-stage sentiment analysis pipeline<br/>
    • EIP status filtering (Final, Living, Draft, Review)<br/>
    • Batch processing for large datasets<br/>
    • Real-time job status tracking<br/>
    • Export functionality for analysis results
    """
    story.append(Paragraph(tech_details, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    print("PDF documentation created: UI_Documentation.pdf")

if __name__ == "__main__":
    create_pdf_documentation()