import os
import time
import requests
from PIL import Image
from io import BytesIO

def capture_screenshots():
    # Create screenshots directory if it doesn't exist
    os.makedirs('documentation/screenshots', exist_ok=True)
    
    # Wait for Streamlit to be fully loaded
    time.sleep(5)
    
    # Pages to capture
    pages = [
        ('main_page', 'http://localhost:5000'),
        ('style_assistant', 'http://localhost:5000/?page=Smart+Style+Assistant'),
        ('my_items', 'http://localhost:5000/?page=My+Items')
    ]
    
    for page_name, url in pages:
        try:
            # Make request to the page
            response = requests.get(url)
            if response.status_code == 200:
                # Save the screenshot
                with open(f'documentation/screenshots/{page_name}.png', 'wb') as f:
                    f.write(response.content)
                print(f"Successfully captured {page_name}")
            else:
                print(f"Failed to capture {page_name}. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error capturing {page_name}: {str(e)}")
        
        # Wait between captures
        time.sleep(2)

if __name__ == "__main__":
    capture_screenshots()