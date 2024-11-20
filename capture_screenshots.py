import os
import requests
from PIL import Image
from io import BytesIO
import time

def capture_screenshots():
    # Create screenshots directory if it doesn't exist
    os.makedirs('documentation/screenshots', exist_ok=True)
    
    base_url = "http://0.0.0.0:5000"
    pages = [
        {"name": "main_page", "path": "/"},
        {"name": "smart_style", "path": "/?nav=Smart+Style+Assistant"},
        {"name": "my_items", "path": "/my_items"}
    ]
    
    try:
        for page in pages:
            # Wait for a moment to ensure the page is loaded
            time.sleep(2)
            
            # Make request to the page
            response = requests.get(f"{base_url}{page['path']}")
            
            if response.status_code == 200:
                # Save the screenshot
                screenshot_path = f"documentation/screenshots/{page['name']}.png"
                with open(screenshot_path, "wb") as f:
                    f.write(response.content)
                print(f"Screenshot saved: {screenshot_path}")
            else:
                print(f"Failed to capture {page['name']}: Status code {response.status_code}")
        
        print("Screenshots captured successfully!")
        
    except Exception as e:
        print(f"Error capturing screenshots: {str(e)}")

if __name__ == "__main__":
    capture_screenshots()