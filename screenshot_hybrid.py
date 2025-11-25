#!/usr/bin/env python3
"""
Hybrid Screenshot Capture System
Combines html2image (fast) with Playwright (reliable) for optimal performance
"""
import asyncio
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# html2image for fast screenshots
try:
    from html2image import Html2Image
    HTML2IMAGE_AVAILABLE = True
except ImportError:
    HTML2IMAGE_AVAILABLE = False

# Playwright for reliable screenshots
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logger = logging.getLogger(__name__)


class HybridScreenshotCapture:
    """Optimized screenshot capture using html2image + Playwright fallback"""
    
    def __init__(self, output_dir: str = "Output/Screenshots", max_concurrent: int = 3):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_concurrent = max_concurrent
        
        # Initialize html2image if available
        if HTML2IMAGE_AVAILABLE:
            self.hti = Html2Image(output_path=str(self.output_dir))
            self.hti.browser.flags = ['--no-sandbox', '--disable-dev-shm-usage']
        
        # Statistics
        self.stats = {
            'total': 0,
            'html2image_success': 0,
            'playwright_success': 0,
            'failed': 0,
            'start_time': None,
            'end_time': None
        }
    
    def is_valid_screenshot(self, file_path: Path) -> bool:
        """Check if screenshot file is valid (not blank/error page)"""
        if not file_path.exists():
            return False
        
        # Check file size (should be > 10KB for a real screenshot)
        size = file_path.stat().st_size
        if size < 10240:  # 10KB minimum
            return False
        
        return True
    
    def capture_with_html2image(self, url: str, filename: str) -> bool:
        """Try fast capture with html2image"""
        if not HTML2IMAGE_AVAILABLE:
            return False
        
        try:
            # Capture with html2image
            self.hti.screenshot(
                url=url,
                save_as=filename,
                size=(1920, 1080)
            )
            
            screenshot_path = self.output_dir / filename
            
            # Validate the screenshot
            if self.is_valid_screenshot(screenshot_path):
                self.stats['html2image_success'] += 1
                return True
            else:
                # Delete invalid screenshot
                if screenshot_path.exists():
                    screenshot_path.unlink()
                return False
                
        except Exception as e:
            logger.debug(f"html2image failed for {url}: {e}")
            return False
    
    async def capture_with_playwright(self, url: str, filename: str) -> bool:
        """Reliable capture with Playwright"""
        if not PLAYWRIGHT_AVAILABLE:
            return False
            
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                page = await context.new_page()
                
                try:
                    await page.goto(url, timeout=30000, wait_until='load')
                    await asyncio.sleep(1)  # Wait for JS to render
                    
                    screenshot_path = self.output_dir / filename
                    await page.screenshot(path=str(screenshot_path), full_page=False)
                    
                    if self.is_valid_screenshot(screenshot_path):
                        self.stats['playwright_success'] += 1
                        return True
                    else:
                        return False
                        
                except PlaywrightTimeout:
                    return False
                except Exception as e:
                    logger.debug(f"Playwright error for {url}: {e}")
                    return False
                finally:
                    await context.close()
                    await browser.close()
                    
        except Exception as e:
            logger.error(f"Failed to capture {url}: {e}")
            return False
    
    async def capture_single(self, url: str, domain: str, content_hash: str = None) -> Dict[str, any]:
        """Capture single screenshot with hybrid approach"""
        self.stats['total'] += 1
        filename = f"{domain.replace('.', '_')}.png"
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        
        result = {
            'domain': domain,
            'url': url,
            'filename': filename,
            'content_hash': content_hash,
            'success': False,
            'method': None
        }
        
        # Step 1: Try html2image (fast method)
        if HTML2IMAGE_AVAILABLE:
            if self.capture_with_html2image(url, filename):
                result['success'] = True
                result['method'] = 'html2image'
                return result
        
        # Step 2: Fallback to Playwright (reliable method)
        if await self.capture_with_playwright(url, filename):
            result['success'] = True
            result['method'] = 'playwright'
            return result
        
        # Both methods failed
        self.stats['failed'] += 1
        return result
    
    async def capture_batch_parallel(self, domains: List[Dict[str, str]]) -> List[Dict[str, any]]:
        """Capture multiple screenshots in parallel batches"""
        self.stats['start_time'] = datetime.now()
        print(f"\n[*] Starting hybrid screenshot capture for {len(domains)} domains")
        print(f"[*] Max concurrent: {self.max_concurrent}")
        
        results = []
        
        # Process in batches for memory efficiency
        for i in range(0, len(domains), self.max_concurrent):
            batch = domains[i:i + self.max_concurrent]
            batch_num = (i // self.max_concurrent) + 1
            total_batches = (len(domains) + self.max_concurrent - 1) // self.max_concurrent
            
            print(f"[*] Processing batch {batch_num}/{total_batches} ({len(batch)} domains)")
            
            # Create tasks for this batch
            tasks = [
                self.capture_single(
                    d.get('url', d['domain']), 
                    d['domain'],
                    d.get('content_hash')
                )
                for d in batch
            ]
            
            # Execute batch in parallel
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle results
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch task failed: {result}")
                    results.append({'success': False, 'error': str(result)})
                else:
                    results.append(result)
        
        self.stats['end_time'] = datetime.now()
        self.print_statistics()
        
        return results
    
    def print_statistics(self):
        """Print capture statistics"""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        print("\n" + "="*60)
        print("SCREENSHOT CAPTURE STATISTICS")
        print("="*60)
        print(f"Total domains:          {self.stats['total']}")
        print(f"[+] html2image success:  {self.stats['html2image_success']} "
              f"({self.stats['html2image_success']/max(self.stats['total'], 1)*100:.1f}%)")
        print(f"[+] Playwright success:  {self.stats['playwright_success']} "
              f"({self.stats['playwright_success']/max(self.stats['total'], 1)*100:.1f}%)")
        print(f"[-] Failed:              {self.stats['failed']} "
              f"({self.stats['failed']/max(self.stats['total'], 1)*100:.1f}%)")
        print(f"[*] Duration:            {duration:.2f}s")
        if self.stats['total'] > 0:
            print(f"[*] Avg per screenshot:  {duration/self.stats['total']:.2f}s")
        print("="*60)
