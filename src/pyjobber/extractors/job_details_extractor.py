"""
Job Details Extractor Module

This module provides functionality to extract detailed job information from URLs.
It attempts to parse HTML content first, and falls back to PDF generation and parsing
if needed.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
from playwright.sync_api import sync_playwright, Page, Browser
import pdfplumber
from bs4 import BeautifulSoup


class JobDetailsExtractor:
    """Extract detailed job information from job posting URLs."""

    def __init__(self, output_dir: str = "data/job_details"):
        """
        Initialize the job details extractor.

        Args:
            output_dir: Directory to store extracted job details and PDFs
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/pdfs", exist_ok=True)
        os.makedirs(f"{output_dir}/markdown", exist_ok=True)

    def extract_html_content(self, url: str, timeout: int = 30000) -> Tuple[bool, Optional[str]]:
        """
        Extract content from URL by parsing HTML.

        Args:
            url: The URL to extract content from
            timeout: Timeout in milliseconds for page load

        Returns:
            Tuple of (success, content) where content is extracted text or None
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(ignore_https_errors=True)
                page = context.new_page()

                print(f"[HTML] Attempting to load {url}")
                page.goto(url, timeout=timeout, wait_until="networkidle")

                # Wait a bit for dynamic content
                page.wait_for_timeout(2000)

                # Get the HTML content
                html_content = page.content()
                browser.close()

                # Parse with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')

                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()

                # Extract text
                text = soup.get_text(separator='\n', strip=True)

                # Clean up excessive newlines
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                content = '\n'.join(lines)

                if len(content) > 100:  # Minimum viable content length
                    print(f"[HTML] Successfully extracted {len(content)} characters")
                    return True, content
                else:
                    print(f"[HTML] Content too short ({len(content)} chars), will try PDF")
                    return False, None

        except Exception as e:
            print(f"[HTML] Failed to extract from {url}: {e}")
            return False, None

    def save_page_as_pdf(self, url: str, job_id: str, use_gdpr_extension: bool = False) -> Optional[str]:
        """
        Save webpage as PDF using Playwright.

        Args:
            url: The URL to save
            job_id: Unique identifier for the job
            use_gdpr_extension: Whether to attempt using GDPR consent extension (requires X server)

        Returns:
            Path to saved PDF or None if failed
        """
        try:
            pdf_path = os.path.join(self.output_dir, "pdfs", f"{job_id}.pdf")

            with sync_playwright() as p:
                print(f"[PDF] Launching browser for {url}")

                # Use headless mode by default (no X server needed)
                # Set headless=False only if explicitly using GDPR extension
                browser = p.chromium.launch(
                    headless=True,  # Changed to True by default
                    args=['--disable-blink-features=AutomationControlled']
                )

                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    ignore_https_errors=True  # Added to handle SSL errors
                )

                page = context.new_page()

                print(f"[PDF] Loading page {url}")
                page.goto(url, timeout=60000, wait_until="networkidle")

                # Wait for page to fully render
                page.wait_for_timeout(5000)

                # Try to handle common cookie consent patterns
                self._handle_cookie_consent(page)

                # Wait a bit more after handling consents
                page.wait_for_timeout(2000)

                print(f"[PDF] Generating PDF...")
                page.pdf(
                    path=pdf_path,
                    format='A4',
                    print_background=True,
                    margin={'top': '1cm', 'right': '1cm', 'bottom': '1cm', 'left': '1cm'}
                )

                browser.close()
                print(f"[PDF] Saved to {pdf_path}")
                return pdf_path

        except Exception as e:
            print(f"[PDF] Failed to save PDF for {url}: {e}")
            return None

    def _handle_cookie_consent(self, page: Page):
        """
        Attempt to handle common cookie consent dialogs.

        Args:
            page: Playwright page object
        """
        # Common selectors for cookie consent buttons
        consent_selectors = [
            'button:has-text("Accept")',
            'button:has-text("Agree")',
            'button:has-text("Accept All")',
            'button:has-text("I Agree")',
            'button:has-text("Allow All")',
            'button[id*="accept"]',
            'button[class*="accept"]',
            'a:has-text("Accept")',
            '.cookie-consent button',
            '#cookie-consent button',
        ]

        for selector in consent_selectors:
            try:
                if page.locator(selector).first.is_visible(timeout=1000):
                    page.locator(selector).first.click()
                    print(f"[PDF] Clicked consent button: {selector}")
                    page.wait_for_timeout(1000)
                    break
            except:
                continue

    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """
        Extract text from PDF using pdfplumber.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text or None if failed
        """
        try:
            print(f"[PDF Parser] Extracting text from {pdf_path}")
            text_lines = []

            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_lines.append(f"--- Page {i + 1} ---")
                        text_lines.append(page_text)
                        text_lines.append("")

            content = '\n'.join(text_lines)
            print(f"[PDF Parser] Extracted {len(content)} characters from {len(pdf.pages)} pages")
            return content

        except Exception as e:
            print(f"[PDF Parser] Failed to extract text from {pdf_path}: {e}")
            return None

    def format_as_markdown(self, content: str, job_title: str, job_url: str) -> str:
        """
        Format extracted content as markdown.

        Args:
            content: The extracted text content
            job_title: Title of the job posting
            job_url: URL of the job posting

        Returns:
            Formatted markdown string
        """
        markdown = f"""# {job_title}

**Source URL:** {job_url}
**Extracted:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Job Details

{content}

---

*This content was automatically extracted from the job posting URL.*
"""
        return markdown

    def extract_job_details(self, job_id: str, job_title: str, job_url: str) -> Dict[str, any]:
        """
        Extract job details using HTML parsing first, then PDF fallback.

        Args:
            job_id: Unique identifier for the job
            job_title: Title of the job posting
            job_url: URL of the job posting

        Returns:
            Dictionary containing extraction results
        """
        result = {
            'job_id': job_id,
            'job_title': job_title,
            'job_url': job_url,
            'method': None,
            'success': False,
            'content': None,
            'markdown': None,
            'pdf_path': None,
            'error': None
        }

        try:
            # Step 1: Try HTML extraction
            print(f"\n{'='*60}")
            print(f"Extracting: {job_title}")
            print(f"URL: {job_url}")
            print(f"{'='*60}")

            html_success, html_content = self.extract_html_content(job_url)

            if html_success and html_content:
                result['method'] = 'html'
                result['success'] = True
                result['content'] = html_content
                result['markdown'] = self.format_as_markdown(html_content, job_title, job_url)

                # Save markdown file
                markdown_path = os.path.join(self.output_dir, "markdown", f"{job_id}.md")
                with open(markdown_path, 'w', encoding='utf-8') as f:
                    f.write(result['markdown'])

                print(f"[SUCCESS] Extracted via HTML and saved to {markdown_path}")
                return result

            # Step 2: Fallback to PDF
            print(f"[FALLBACK] Attempting PDF extraction...")
            pdf_path = self.save_page_as_pdf(job_url, job_id, use_gdpr_extension=False)

            if pdf_path and os.path.exists(pdf_path):
                result['pdf_path'] = pdf_path

                # Extract text from PDF
                pdf_content = self.extract_text_from_pdf(pdf_path)

                if pdf_content:
                    result['method'] = 'pdf'
                    result['success'] = True
                    result['content'] = pdf_content
                    result['markdown'] = self.format_as_markdown(pdf_content, job_title, job_url)

                    # Save markdown file
                    markdown_path = os.path.join(self.output_dir, "markdown", f"{job_id}.md")
                    with open(markdown_path, 'w', encoding='utf-8') as f:
                        f.write(result['markdown'])

                    print(f"[SUCCESS] Extracted via PDF and saved to {markdown_path}")
                    return result
                else:
                    result['error'] = "PDF created but text extraction failed"
            else:
                result['error'] = "Failed to create PDF"

        except Exception as e:
            result['error'] = str(e)
            print(f"[ERROR] Extraction failed: {e}")

        return result

    def extract_multiple_jobs(self, jobs_df: pd.DataFrame) -> List[Dict]:
        """
        Extract details for multiple jobs from a DataFrame.

        Args:
            jobs_df: DataFrame containing job information with 'id', 'title', 'ownApplyUrl' columns

        Returns:
            List of extraction results
        """
        results = []
        total = len(jobs_df)

        print(f"\n{'#'*60}")
        print(f"Starting extraction for {total} jobs")
        print(f"{'#'*60}\n")

        for idx, row in jobs_df.iterrows():
            job_id = str(row.get('id', idx))
            job_title = row.get('title', 'Unknown Title')
            job_url = row.get('ownApplyUrl', '')

            if not job_url:
                print(f"[SKIP] No URL for job: {job_title}")
                continue

            print(f"\n[Progress: {idx + 1}/{total}]")
            result = self.extract_job_details(job_id, job_title, job_url)
            results.append(result)

        # Summary
        successful = sum(1 for r in results if r['success'])
        print(f"\n{'#'*60}")
        print(f"Extraction Complete: {successful}/{len(results)} successful")
        print(f"{'#'*60}\n")

        return results


def load_selected_jobs(csv_path: str = "data/selected/selected_jobs_export.csv") -> Optional[pd.DataFrame]:
    """
    Load selected jobs from CSV file.

    Args:
        csv_path: Path to the selected jobs CSV file

    Returns:
        DataFrame of selected jobs or None if file doesn't exist
    """
    if not os.path.exists(csv_path):
        print(f"[ERROR] Selected jobs file not found: {csv_path}")
        return None

    try:
        df = pd.read_csv(csv_path)
        print(f"[INFO] Loaded {len(df)} selected jobs from {csv_path}")
        return df
    except Exception as e:
        print(f"[ERROR] Failed to load selected jobs: {e}")
        return None
