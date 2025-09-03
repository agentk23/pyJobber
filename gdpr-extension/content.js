const GDPR_SELECTORS = {
            // Accept buttons
            acceptButtons: [
                '[id*="accept"]', '[class*="accept"]', '[data-testid*="accept"]',
                '[id*="agree"]', '[class*="agree"]', '[data-testid*="agree"]',
                '[id*="consent"]', '[class*="consent"]', '[data-testid*="consent"]',
                'button[title*="Accept"]', 'button[aria-label*="Accept"]',
                'button:contains("Accept")', 'button:contains("Agree")',
                'button:contains("OK")', 'button:contains("Got it")',
                'button:contains("Allow")', 'button:contains("Continue")',
                // Multi-language support
                'button:contains("Akzeptieren")', 'button:contains("Accepter")',
                'button:contains("Aceptar")', 'button:contains("Accetta")',
                'button:contains("Aceitar")', 'button:contains("Принять")',
                // CSS classes commonly used
                '.cookie-accept', '.gdpr-accept', '.consent-accept',
                '.cookie-ok', '.privacy-accept', '.banner-accept'
            ],
            
            // Cookie banners/modals to hide
            banners: [
                '[id*="cookie"]', '[class*="cookie"]', '[data-testid*="cookie"]',
                '[id*="gdpr"]', '[class*="gdpr"]', '[data-testid*="gdpr"]',
                '[id*="consent"]', '[class*="consent"]', '[data-testid*="consent"]',
                '[id*="privacy"]', '[class*="privacy"]', '[data-testid*="privacy"]',
                '.cookie-banner', '.gdpr-banner', '.consent-banner',
                '.cookie-notice', '.privacy-notice', '.consent-modal',
                '#cookieConsent', '#gdprConsent', '#privacyBanner'
            ],
            
            // Close/dismiss buttons
            closeButtons: [
                '[aria-label*="close"]', '[aria-label*="dismiss"]',
                '[title*="close"]', '[title*="dismiss"]',
                '.close', '.dismiss', '.cookie-close',
                'button[class*="close"]', '[data-dismiss]'
            ]
        };
        
        function clickElement(element) {
            if (element && element.offsetParent !== null) {
                try {
                    element.click();
                    return true;
                } catch (e) {
                    try {
                        element.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                        return true;
                    } catch (e2) {
                        return false;
                    }
                }
            }
            return false;
        }
        
        function handleGDPRPopups() {
            // First try to click accept buttons
            for (const selector of GDPR_SELECTORS.acceptButtons) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (clickElement(element)) {
                        console.log('GDPR: Clicked accept button:', selector);
                        return true;
                    }
                }
            }
            
            // If no accept button found, try close buttons
            for (const selector of GDPR_SELECTORS.closeButtons) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (clickElement(element)) {
                        console.log('GDPR: Clicked close button:', selector);
                        return true;
                    }
                }
            }
            
            // Last resort: hide the banners with CSS
            for (const selector of GDPR_SELECTORS.banners) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element.offsetParent !== null) {
                        element.style.display = 'none !important';
                        console.log('GDPR: Hidden banner:', selector);
                    }
                }
            }
            
            return false;
        }
        
        // Run immediately
        handleGDPRPopups();
        
        // Run after DOM loads
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', handleGDPRPopups);
        }
        
        // Run periodically for dynamic content
        const observer = new MutationObserver(() => {
            handleGDPRPopups();
        });
        
        observer.observe(document.body || document.documentElement, {
            childList: true,
            subtree: true
        });
        
        // Also run with delays for slow-loading popups
        setTimeout(handleGDPRPopups, 1000);
        setTimeout(handleGDPRPopups, 3000);
        setTimeout(handleGDPRPopups, 5000);