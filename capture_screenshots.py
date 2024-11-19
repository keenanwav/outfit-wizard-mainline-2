import os
import time
import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(options=chrome_options)

def capture_screenshots():
    # Create screenshots directory if it doesn't exist
    os.makedirs('documentation/screenshots', exist_ok=True)
    
    # Initialize webdriver
    driver = setup_driver()
    
    # Pages to capture
    pages = [
        ('main_page_outfit_generation', 'http://0.0.0.0:5000'),
        ('smart_style_assistant', 'http://0.0.0.0:5000/?page=Smart+Style+Assistant'),
        ('my_items', 'http://0.0.0.0:5000/?page=My+Items')
    ]
    
    try:
        for page_name, url in pages:
            # Navigate to page
            driver.get(url)
            # Wait for content to load
            time.sleep(5)
            
            # Take screenshot
            screenshot_path = f'documentation/screenshots/{page_name}.png'
            driver.save_screenshot(screenshot_path)
            print(f"Successfully captured {page_name}")
            
            # Wait between captures
            time.sleep(2)
    except Exception as e:
        print(f"Error capturing screenshots: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    capture_screenshots()
