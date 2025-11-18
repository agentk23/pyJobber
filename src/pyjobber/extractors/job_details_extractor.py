"""
Job Details Extractor Module

This module provides functionality to extract detailed job information from URLs.
It attempts to parse HTML content first, and falls back to PDF generation and parsing
if needed.

The extractor intelligently parses job postings to extract:
- Job requirements and qualifications
- Job description and responsibilities
- Recruitment process information
- Company information and culture
- Location and work mode (remote/hybrid/office)
- Company name
"""

import os
import tempfile
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
from playwright.sync_api import sync_playwright, Page, Browser
import pdfplumber
from bs4 import BeautifulSoup, Tag


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

    def parse_structured_job_data(self, soup: BeautifulSoup, raw_text: str) -> Dict[str, any]:
        """
        Parse HTML to extract structured job information.

        Args:
            soup: BeautifulSoup object of the page
            raw_text: Raw text content extracted from the page

        Returns:
            Dictionary with structured job data
        """
        data = {
            'company_name': None,
            'location': None,
            'work_mode': None,  # remote/hybrid/office
            'job_requirements': [],
            'job_description': [],
            'recruitment_process': [],
            'company_looking_for': [],
            'raw_sections': {}
        }

        # Extract company name
        data['company_name'] = self._extract_company_name(soup, raw_text)

        # Extract location
        data['location'] = self._extract_location(soup, raw_text)

        # Extract work mode
        data['work_mode'] = self._extract_work_mode(soup, raw_text)

        # Extract structured sections from text
        sections = self._identify_sections(raw_text)
        data['raw_sections'] = sections

        # Parse requirements
        data['job_requirements'] = self._extract_requirements(sections, raw_text)

        # Parse job description/responsibilities
        data['job_description'] = self._extract_description(sections, raw_text)

        # Parse recruitment process
        data['recruitment_process'] = self._extract_recruitment_process(sections, raw_text)

        # Parse what company is looking for
        data['company_looking_for'] = self._extract_looking_for(sections, raw_text)

        return data

    def _extract_company_name(self, soup: BeautifulSoup, text: str) -> Optional[str]:
        """Extract company name from page."""
        # Try meta tags first
        for meta in soup.find_all('meta'):
            if meta.get('property') == 'og:site_name' or meta.get('name') == 'author':
                if meta.get('content'):
                    return meta.get('content').strip()

        # Try common selectors
        selectors = [
            'h1.company-name', '.company-name', '#company-name',
            '[data-company]', '.employer-name', '.company-title'
        ]
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)

        # Try pattern matching in text
        company_patterns = [
            r'About\s+([A-Z][A-Za-z\s&]+(?:Inc|LLC|Ltd|GmbH|SRL)?)',
            r'Company:\s*([A-Z][A-Za-z\s&]+)',
            r'Employer:\s*([A-Z][A-Za-z\s&]+)'
        ]
        for pattern in company_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return None

    def _extract_location(self, soup: BeautifulSoup, text: str) -> Optional[str]:
        """Extract job location."""
        # Try common selectors
        selectors = [
            '.location', '#location', '[data-location]',
            '.job-location', '.work-location', 'span.location'
        ]
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)

        # Try pattern matching
        location_patterns = [
            r'Location:\s*([A-Za-z\s,]+(?:Romania|RO|Cluj|Bucharest|Remote)?)',
            r'(?:City|Office):\s*([A-Za-z\s,]+)',
            r'Based in\s+([A-Za-z\s,]+)'
        ]
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_work_mode(self, soup: BeautifulSoup, text: str) -> Optional[str]:
        """Extract work mode (remote/hybrid/office)."""
        text_lower = text.lower()

        # Check for explicit mentions
        if any(word in text_lower for word in ['full remote', 'fully remote', '100% remote', 'remote work']):
            return 'Remote'
        elif any(word in text_lower for word in ['hybrid', 'flexible', 'partly remote']):
            return 'Hybrid'
        elif any(word in text_lower for word in ['on-site', 'onsite', 'office-based', 'in office']):
            return 'Office'

        return None

    def _identify_sections(self, text: str) -> Dict[str, str]:
        """Identify and extract major sections from the job posting."""
        sections = {}

        # Common section headers
        section_patterns = {
            'requirements': r'(?:Requirements|Qualifications|Must Have|Essential Skills|Required Skills)[:\s]*\n((?:.*\n){1,50})',
            'responsibilities': r'(?:Responsibilities|What you.?ll do|Your role|Job Description|Duties)[:\s]*\n((?:.*\n){1,50})',
            'nice_to_have': r'(?:Nice to have|Preferred|Bonus|Plus|Would be great)[:\s]*\n((?:.*\n){1,20})',
            'benefits': r'(?:Benefits|We offer|Perks|What we offer)[:\s]*\n((?:.*\n){1,30})',
            'about_company': r'(?:About us|About the company|Who we are|Our company)[:\s]*\n((?:.*\n){1,30})',
            'recruitment': r'(?:Recruitment process|Interview process|How we hire|Application process)[:\s]*\n((?:.*\n){1,20})',
            'looking_for': r'(?:We are looking for|We need|Ideal candidate|The right person)[:\s]*\n((?:.*\n){1,30})'
        }

        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                content = match.group(1).strip()
                # Stop at next section header
                next_header = re.search(r'\n(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*:|\n[A-Z][A-Z\s]+\n)', content)
                if next_header:
                    content = content[:next_header.start()].strip()
                sections[section_name] = content

        return sections

    def _extract_requirements(self, sections: Dict[str, str], text: str) -> List[str]:
        """Extract job requirements."""
        requirements = []

        # Check identified sections
        for key in ['requirements', 'qualifications']:
            if key in sections:
                requirements.extend(self._parse_bullet_points(sections[key]))

        # Also look for explicit requirement bullets
        req_pattern = r'(?:Required|Must have|Essential):\s*((?:[-•*]\s*.+\n?)+)'
        matches = re.findall(req_pattern, text, re.IGNORECASE)
        for match in matches:
            requirements.extend(self._parse_bullet_points(match))

        return list(set(requirements))  # Remove duplicates

    def _extract_description(self, sections: Dict[str, str], text: str) -> List[str]:
        """Extract job description and responsibilities."""
        description = []

        for key in ['responsibilities', 'job_description']:
            if key in sections:
                description.extend(self._parse_bullet_points(sections[key]))

        return list(set(description))

    def _extract_recruitment_process(self, sections: Dict[str, str], text: str) -> List[str]:
        """Extract recruitment process information."""
        process = []

        if 'recruitment' in sections:
            process.extend(self._parse_bullet_points(sections['recruitment']))

        # Look for numbered steps
        step_pattern = r'(?:Step\s+\d+|Stage\s+\d+|\d+\.):\s*(.+)'
        matches = re.findall(step_pattern, text, re.IGNORECASE)
        process.extend([m.strip() for m in matches])

        return process

    def _extract_looking_for(self, sections: Dict[str, str], text: str) -> List[str]:
        """Extract what the company is looking for."""
        looking_for = []

        if 'looking_for' in sections:
            looking_for.extend(self._parse_bullet_points(sections['looking_for']))

        # Parse "ideal candidate" mentions
        ideal_pattern = r'(?:ideal candidate|perfect fit|right person)(?:\s+is|\s+has|\s+will)(.{10,200})'
        matches = re.findall(ideal_pattern, text, re.IGNORECASE)
        looking_for.extend([m.strip() for m in matches])

        return looking_for

    def _parse_bullet_points(self, text: str) -> List[str]:
        """Parse bullet points from text."""
        bullets = []

        # Match common bullet formats
        bullet_patterns = [
            r'[-•*▪]\s*(.+)',
            r'^\d+\.\s*(.+)',
            r'^[A-Z][a-z]+(?:\s+[a-z]+)*:\s*(.+)'
        ]

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            for pattern in bullet_patterns:
                match = re.match(pattern, line)
                if match:
                    bullets.append(match.group(1).strip())
                    break
            else:
                # If line is substantial and not a header, include it
                if len(line) > 15 and not line.endswith(':'):
                    bullets.append(line)

        return bullets

    def extract_html_content(self, url: str, timeout: int = 30000) -> Tuple[bool, Optional[Dict]]:
        """
        Extract structured content from URL by parsing HTML.

        Args:
            url: The URL to extract content from
            timeout: Timeout in milliseconds for page load

        Returns:
            Tuple of (success, structured_data) where structured_data is a Dict or None
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
                raw_text = '\n'.join(lines)

                if len(raw_text) > 100:  # Minimum viable content length
                    print(f"[HTML] Successfully extracted {len(raw_text)} characters")
                    print(f"[HTML] Parsing structured job data...")

                    # Parse structured data
                    structured_data = self.parse_structured_job_data(soup, raw_text)
                    structured_data['raw_text'] = raw_text  # Keep raw text for reference

                    return True, structured_data
                else:
                    print(f"[HTML] Content too short ({len(raw_text)} chars), will try PDF")
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

    def format_structured_data_as_markdown(self, data: Dict, job_title: str, job_url: str) -> str:
        """
        Format structured job data as markdown.

        Args:
            data: Structured job data dictionary
            job_title: Title of the job posting
            job_url: URL of the job posting

        Returns:
            Formatted markdown string
        """
        sections = []

        # Header
        sections.append(f"# {job_title}\n")
        sections.append(f"**Source URL:** {job_url}")
        sections.append(f"**Extracted:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        sections.append("---\n")

        # Company & Location Info
        sections.append("## 📍 Job Information\n")
        if data.get('company_name'):
            sections.append(f"**Company:** {data['company_name']}")
        if data.get('location'):
            sections.append(f"**Location:** {data['location']}")
        if data.get('work_mode'):
            sections.append(f"**Work Mode:** {data['work_mode']}")
        sections.append("")

        # Job Requirements
        if data.get('job_requirements'):
            sections.append("## ✅ Requirements & Qualifications\n")
            for req in data['job_requirements']:
                sections.append(f"- {req}")
            sections.append("")

        # Job Description/Responsibilities
        if data.get('job_description'):
            sections.append("## 📋 Responsibilities & Job Description\n")
            for desc in data['job_description']:
                sections.append(f"- {desc}")
            sections.append("")

        # What Company is Looking For
        if data.get('company_looking_for'):
            sections.append("## 🎯 What We're Looking For\n")
            for item in data['company_looking_for']:
                sections.append(f"- {item}")
            sections.append("")

        # Recruitment Process
        if data.get('recruitment_process'):
            sections.append("## 📊 Recruitment Process\n")
            for i, step in enumerate(data['recruitment_process'], 1):
                sections.append(f"{i}. {step}")
            sections.append("")

        # Additional Sections
        if data.get('raw_sections'):
            if 'benefits' in data['raw_sections']:
                sections.append("## 💰 Benefits & Perks\n")
                sections.append(data['raw_sections']['benefits'])
                sections.append("")

            if 'about_company' in data['raw_sections']:
                sections.append("## 🏢 About the Company\n")
                sections.append(data['raw_sections']['about_company'])
                sections.append("")

            if 'nice_to_have' in data['raw_sections']:
                sections.append("## ⭐ Nice to Have\n")
                sections.append(data['raw_sections']['nice_to_have'])
                sections.append("")

        sections.append("---\n")
        sections.append("*This content was automatically extracted and parsed from the job posting URL.*")

        return '\n'.join(sections)

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

            html_success, structured_data = self.extract_html_content(job_url)

            if html_success and structured_data:
                result['method'] = 'html'
                result['success'] = True
                result['content'] = structured_data  # Store structured data
                result['markdown'] = self.format_structured_data_as_markdown(structured_data, job_title, job_url)

                # Save markdown file
                markdown_path = os.path.join(self.output_dir, "markdown", f"{job_id}.md")
                with open(markdown_path, 'w', encoding='utf-8') as f:
                    f.write(result['markdown'])

                print(f"[SUCCESS] Extracted via HTML and saved to {markdown_path}")
                print(f"  - Company: {structured_data.get('company_name', 'N/A')}")
                print(f"  - Location: {structured_data.get('location', 'N/A')}")
                print(f"  - Work Mode: {structured_data.get('work_mode', 'N/A')}")
                print(f"  - Requirements: {len(structured_data.get('job_requirements', []))} items")
                print(f"  - Responsibilities: {len(structured_data.get('job_description', []))} items")
                return result

            # Step 2: Fallback to PDF
            print(f"[FALLBACK] Attempting PDF extraction...")
            pdf_path = self.save_page_as_pdf(job_url, job_id, use_gdpr_extension=False)

            if pdf_path and os.path.exists(pdf_path):
                result['pdf_path'] = pdf_path

                # Extract text from PDF
                pdf_text = self.extract_text_from_pdf(pdf_path)

                if pdf_text:
                    # Parse PDF text to structured data
                    print(f"[PDF] Parsing structured data from extracted text...")
                    from bs4 import BeautifulSoup
                    # Create a minimal soup for consistency, but use text parsing
                    soup = BeautifulSoup('', 'html.parser')
                    structured_data = self.parse_structured_job_data(soup, pdf_text)
                    structured_data['raw_text'] = pdf_text

                    result['method'] = 'pdf'
                    result['success'] = True
                    result['content'] = structured_data
                    result['markdown'] = self.format_structured_data_as_markdown(structured_data, job_title, job_url)

                    # Save markdown file
                    markdown_path = os.path.join(self.output_dir, "markdown", f"{job_id}.md")
                    with open(markdown_path, 'w', encoding='utf-8') as f:
                        f.write(result['markdown'])

                    print(f"[SUCCESS] Extracted via PDF and saved to {markdown_path}")
                    print(f"  - Company: {structured_data.get('company_name', 'N/A')}")
                    print(f"  - Location: {structured_data.get('location', 'N/A')}")
                    print(f"  - Work Mode: {structured_data.get('work_mode', 'N/A')}")
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
