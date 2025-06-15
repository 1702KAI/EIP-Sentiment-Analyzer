
#!/usr/bin/env python3
import sys
import os
from screenshot_generator import UIScreenshotGenerator
import logging

def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Starting UI Screenshot PDF Generation...")
    print("📋 This will capture screenshots of all main pages and create a PDF report")
    
    # Check if server is running
    try:
        import requests
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code != 200:
            print("⚠️  Server might not be running properly")
    except:
        print("❌ Cannot connect to http://localhost:5000")
        print("   Please make sure your Flask application is running")
        print("   Run: python app.py")
        return
    
    # Generate screenshots and PDF
    try:
        generator = UIScreenshotGenerator(base_url="http://localhost:5000")
        pdf_path = generator.generate_complete_report()
        
        if pdf_path and os.path.exists(pdf_path):
            print(f"✅ Success! PDF generated: {pdf_path}")
            print(f"📄 File size: {os.path.getsize(pdf_path) / 1024:.1f} KB")
            
            # Try to open the file
            if sys.platform.startswith('linux'):
                os.system(f"xdg-open {pdf_path}")
            elif sys.platform.startswith('darwin'):
                os.system(f"open {pdf_path}")
            elif sys.platform.startswith('win'):
                os.system(f"start {pdf_path}")
                
        else:
            print("❌ Failed to generate PDF")
            
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        logging.error(f"Generation failed: {e}")

if __name__ == "__main__":
    main()
