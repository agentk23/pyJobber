import os
import json
from playwright.async_api import async_playwright
from pathlib import Path

class GDPRBlockerExtension:
    def __init__(self):
        self.extension_path = "./gdpr-extension"


    async def download_cookie_extension(self):
        """Download and setup 'I don't care about cookies' extension"""
        extension_dir = Path(self.extension_path)
        extension_dir.mkdir(exist_ok=True)
    

    async def setup_browser_with_gdpr_blocker(self, playwright):
        """Setup browser with GDPR cookie popup blocker"""
        # Ensure extension exists
        if not os.path.exists(self.extension_path):
            await self.download_cookie_extension()
        
        browser = await playwright.chromium.launch_persistent_context(
            user_data_dir="./browser-persistance-data",
            headless=False,  # Extensions need visible browser
            args=[
                f"--load-extension={self.extension_path}",
                f"--disable-extensions-except={self.extension_path}",
                "--no-first-run",
                "--disable-default-apps",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage"
            ],
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        return browser

    async def manual_gdpr_handler(self, page):
        gdpr_selectors = [
            # Accept buttons
            'button:has-text("Accept")', 'button:has-text("Agree")', 
            'button:has-text("OK")', 'button:has-text("Got it")',
            'button:has-text("Allow all")', 'button:has-text("Accept all")',
            
            # Multi-language
            'button:has-text("Akzeptieren")', 'button:has-text("Accepter")',
            'button:has-text("Aceptar")', 'button:has-text("Accetta")',
            
            # CSS selectors
            '[id*="accept"]:visible', '[class*="accept"]:visible',
            '[data-testid*="accept"]:visible', '.cookie-accept:visible',
            '#acceptCookies:visible', '#cookieAccept:visible',
            
            # Close buttons as fallback
            '[aria-label*="close"]:visible', '[title*="close"]:visible',
            '.cookie-close:visible', '.gdpr-close:visible'
        ]
        
        for selector in gdpr_selectors:
            try:
                element = page.locator(selector).first
                if await element.is_visible(timeout=1000):
                    await element.click()
                    print(f"✅ Clicked GDPR element: {selector}")
                    await page.wait_for_timeout(500)  # Wait for popup to disappear
                    return True
            except:
                continue
        
        return False

    