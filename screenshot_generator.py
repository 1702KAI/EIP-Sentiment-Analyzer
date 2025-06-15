
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import logging

class UIScreenshotGenerator:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.screenshots_dir = "screenshots"
        self.setup_driver()
        self.setup_directories()
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            logging.info("✅ WebDriver initialized successfully")
        except Exception as e:
            logging.error(f"❌ Failed to initialize WebDriver: {e}")
            raise
    
    def setup_directories(self):
        """Create necessary directories"""
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
    def capture_page_screenshot(self, url, filename, description=""):
        """Capture screenshot of a specific page"""
        try:
            full_url = f"{self.base_url}{url}" if not url.startswith('http') else url
            logging.info(f"📸 Capturing screenshot of: {full_url}")
            
            self.driver.get(full_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Wait for any dynamic content
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                pass  # Continue even if wait fails
            
            # Take screenshot
            screenshot_path = os.path.join(self.screenshots_dir, f"{filename}.png")
            self.driver.save_screenshot(screenshot_path)
            
            logging.info(f"✅ Screenshot saved: {screenshot_path}")
            return screenshot_path, description or url
            
        except Exception as e:
            logging.error(f"❌ Failed to capture screenshot for {url}: {e}")
            return None, description or url
    
    def capture_all_pages(self):
        """Capture screenshots of all main pages"""
        pages_to_capture = [
            ("/", "homepage", "Home Page - Landing page with application overview"),
            ("/login", "login_page", "Login Page - User authentication interface"),
            ("/upload", "upload_page", "Upload Page - CSV file upload interface"),
            ("/dashboard", "dashboard", "Dashboard - Analysis job management and overview"),
            ("/results", "results_page", "Results Page - Sentiment analysis results display"),
            ("/smart_contract", "smart_contract", "Smart Contract Generator - AI-powered contract generation"),
        ]
        
        captured_screenshots = []
        
        for url, filename, description in pages_to_capture:
            screenshot_path, desc = self.capture_page_screenshot(url, filename, description)
            if screenshot_path and os.path.exists(screenshot_path):
                captured_screenshots.append((screenshot_path, desc))
                
        return captured_screenshots
    
    def create_pdf_report(self, screenshots, output_filename="UI_Screenshots_Report.pdf"):
        """Create PDF report with screenshots"""
        try:
            doc = SimpleDocTemplate(output_filename, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=1  # Center alignment
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                spaceBefore=20
            )
            
            # Title page
            story.append(Paragraph("EIP Sentiment Analysis Platform", title_style))
            story.append(Paragraph("User Interface Documentation", styles['Heading2']))
            story.append(Spacer(1, 0.5*inch))
            
            # Add metadata
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            story.append(Paragraph(f"Generated on: {current_time}", styles['Normal']))
            story.append(Paragraph(f"Total Pages Captured: {len(screenshots)}", styles['Normal']))
            story.append(Spacer(1, 0.5*inch))
            
            # Add overview
            overview_text = """
            This document contains screenshots of the EIP Sentiment Analysis Platform's user interface.
            The platform provides comprehensive sentiment analysis of Ethereum Improvement Proposals (EIPs)
            with AI-powered smart contract generation capabilities.
            
            Key Features:
            • CSV file upload for community comments analysis
            • VADER sentiment analysis with EIP metadata integration
            • Real-time job processing and status tracking
            • Interactive dashboard with visualization
            • AI-powered smart contract generation
            • Security analysis and test generation
            """
            
            story.append(Paragraph("Overview", heading_style))
            story.append(Paragraph(overview_text, styles['Normal']))
            story.append(PageBreak())
            
            # Add screenshots
            for i, (screenshot_path, description) in enumerate(screenshots, 1):
                try:
                    story.append(Paragraph(f"Page {i}: {description}", heading_style))
                    story.append(Spacer(1, 0.2*inch))
                    
                    # Add image
                    img = Image(screenshot_path)
                    
                    # Scale image to fit page
                    img_width, img_height = img.wrap(0, 0)
                    max_width = 7*inch
                    max_height = 9*inch
                    
                    scale = min(max_width/img_width, max_height/img_height)
                    img.drawWidth = img_width * scale
                    img.drawHeight = img_height * scale
                    
                    story.append(img)
                    story.append(Spacer(1, 0.3*inch))
                    
                    # Add page break except for last image
                    if i < len(screenshots):
                        story.append(PageBreak())
                        
                except Exception as e:
                    logging.error(f"❌ Failed to add screenshot {screenshot_path} to PDF: {e}")
                    story.append(Paragraph(f"Error loading screenshot: {description}", styles['Normal']))
            
            # Build PDF
            doc.build(story)
            logging.info(f"✅ PDF report created: {output_filename}")
            return output_filename
            
        except Exception as e:
            logging.error(f"❌ Failed to create PDF report: {e}")
            return None
    
    def generate_complete_report(self):
        """Generate complete screenshot report"""
        try:
            logging.info("🚀 Starting UI screenshot generation...")
            
            # Capture all screenshots
            screenshots = self.capture_all_pages()
            
            if not screenshots:
                logging.error("❌ No screenshots captured")
                return None
            
            # Create PDF report
            pdf_filename = f"EIP_Platform_UI_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = self.create_pdf_report(screenshots, pdf_filename)
            
            return pdf_path
            
        except Exception as e:
            logging.error(f"❌ Failed to generate report: {e}")
            return None
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

def main():
    """Main function to run screenshot generation"""
    logging.basicConfig(level=logging.INFO)
    
    generator = UIScreenshotGenerator(base_url="http://localhost:5000")
    pdf_path = generator.generate_complete_report()
    
    if pdf_path:
        print(f"✅ PDF report generated successfully: {pdf_path}")
        return pdf_path
    else:
        print("❌ Failed to generate PDF report")
        return None

if __name__ == "__main__":
    main()
