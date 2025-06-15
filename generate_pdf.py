#!/usr/bin/env python3

import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from PIL import Image as PILImage

def create_documentation_pdf():
    """Create PDF documentation using existing screenshots"""
    
    doc = SimpleDocTemplate("EIP_Sentiment_Analyzer_UI_Documentation.pdf", pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.darkblue,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.darkgreen
    )
    
    # Title page
    story.append(Paragraph("EIP Sentiment Analyzer", title_style))
    story.append(Paragraph("User Interface Documentation", styles['Heading2']))
    story.append(Spacer(1, 0.5*inch))
    
    # Overview
    story.append(Paragraph("Application Overview", heading_style))
    overview = """
    The EIP Sentiment Analyzer is a comprehensive Flask web application designed for advanced 
    smart contract analysis and Ethereum Improvement Proposal (EIP) evaluation. The application 
    leverages AI-powered insights and sentiment analysis to provide valuable feedback on blockchain 
    development standards.
    """
    story.append(Paragraph(overview, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Features
    story.append(Paragraph("Key Features", heading_style))
    features = """
    <b>Public Features:</b><br/>
    • Smart Contract Generator with AI-powered EIP recommendations<br/>
    • Interactive Dashboard with sentiment visualizations<br/>
    • EIP status filtering (Final, Living, Draft, Review)<br/>
    • Sentiment-based warnings for code standards<br/>
    
    <b>Admin Features:</b><br/>
    • CSV file upload for sentiment analysis<br/>
    • Three-stage analysis pipeline processing<br/>
    • Results management and data exports<br/>
    • Job status tracking and monitoring<br/>
    """
    story.append(Paragraph(features, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Technology stack
    story.append(Paragraph("Technology Stack", heading_style))
    tech_stack = """
    • Flask web framework with Python backend<br/>
    • PostgreSQL database for data persistence<br/>
    • OpenAI GPT-4o for AI-powered analysis<br/>
    • Bootstrap dark theme for responsive UI<br/>
    • Chart.js for interactive data visualizations<br/>
    • NLTK for sentiment analysis processing<br/>
    • Flask-Login for authentication and session management
    """
    story.append(Paragraph(tech_stack, styles['Normal']))
    story.append(PageBreak())
    
    # Page screenshots with descriptions
    pages = [
        {
            'title': 'Homepage - Landing Page',
            'file': 'home.png',
            'description': """
            The main landing page presents the application's core features to users. Public users can 
            access the Smart Contract Generator and Dashboard, while admin login provides access to 
            additional features like CSV upload and results management. The interface uses a clean, 
            card-based layout with clear navigation and feature descriptions.
            """
        },
        {
            'title': 'Smart Contract Generator',
            'file': 'smart_contracts.png',
            'description': """
            The Smart Contract Generator is the application's flagship feature, providing AI-powered 
            smart contract generation and analysis. Users can generate contracts from EIP specifications, 
            analyze existing code for security vulnerabilities, and receive EIP recommendations with 
            sentiment-based warnings. The interface includes multiple analysis modes and EIP status filtering.
            """
        },
        {
            'title': 'Interactive Dashboard',
            'file': 'dashboard.png',
            'description': """
            The Dashboard provides comprehensive visualizations of EIP sentiment analysis data. Users can 
            explore sentiment trends across different EIP categories and statuses through interactive charts. 
            The dashboard includes filtering options and data export capabilities, making it accessible to 
            both technical and non-technical users.
            """
        },
        {
            'title': 'Admin Login Portal',
            'file': 'login.png',
            'description': """
            The admin login portal provides secure access to administrative features. Administrators can 
            upload CSV files for sentiment analysis, manage analysis jobs, and access detailed results. 
            The login interface includes clear instructions and credential requirements for admin access.
            """
        }
    ]
    
    for page in pages:
        story.append(Paragraph(page['title'], heading_style))
        story.append(Paragraph(page['description'], styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Add screenshot if it exists
        screenshot_path = f"screenshots/{page['file']}"
        if os.path.exists(screenshot_path):
            try:
                # Get image dimensions and scale appropriately
                with PILImage.open(screenshot_path) as img:
                    width, height = img.size
                    # Scale to fit page width with margins
                    max_width = 6.5 * inch
                    max_height = 8 * inch
                    
                    scale = min(max_width / width, max_height / height)
                    new_width = width * scale
                    new_height = height * scale
                
                story.append(Image(screenshot_path, width=new_width, height=new_height))
                
            except Exception as e:
                story.append(Paragraph(f"Screenshot unavailable: {e}", styles['Normal']))
        else:
            story.append(Paragraph("Screenshot not found", styles['Normal']))
            
        story.append(PageBreak())
    
    # Access control information
    story.append(Paragraph("Access Control & Security", heading_style))
    access_info = """
    <b>Public Access:</b><br/>
    • Homepage with feature overview and navigation<br/>
    • Smart Contract Generator for AI-powered analysis<br/>
    • Dashboard with sentiment data visualizations<br/>
    
    <b>Administrator Access:</b><br/>
    • CSV file upload for sentiment analysis processing<br/>
    • Analysis job management and status monitoring<br/>
    • Results viewing and data export capabilities<br/>
    • Administrative dashboard features<br/>
    
    <b>Authentication:</b><br/>
    Admin credentials are required for protected features:<br/>
    • admin@example.com / admin123<br/>
    • admin@sentiment.com / password123<br/>
    
    The application implements role-based access control with Flask-Login 
    for session management and secure authentication handling.
    """
    story.append(Paragraph(access_info, styles['Normal']))
    
    # Build the PDF
    doc.build(story)
    return "EIP_Sentiment_Analyzer_UI_Documentation.pdf"

if __name__ == "__main__":
    pdf_file = create_documentation_pdf()
    print(f"Documentation PDF created: {pdf_file}")