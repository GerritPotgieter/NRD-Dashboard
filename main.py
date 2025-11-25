#!/usr/bin/env python3
"""
NRD2 Main Workflow - Minimal Essential Pipeline
Streamlined execution of: Download -> Parse -> Filter -> Scan -> Screenshot
"""

import os
import re
import csv
import sys
import json
import time
import base64
import hashlib
import requests
import zipfile
import asyncio
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Set, Optional

# Add backend directory to path for imports
BACKEND_DIR = Path(__file__).parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

try:
    from db_manager import get_db
except ImportError:
    print("[!] db_manager not found - run from project root directory")
    sys.exit(1)

# Try to import hybrid screenshot module
try:
    from screenshot_hybrid import HybridScreenshotCapture
    SCREENSHOT_AVAILABLE = True
except ImportError:
    SCREENSHOT_AVAILABLE = False
    print("[!] Screenshot modules not available - screenshots will be skipped")

# ============================================================================
# CONFIGURATION
# ============================================================================

ROOT_DIR = Path(__file__).parent.absolute()
DAILY_DIR = ROOT_DIR / "Domain_Downloads"
OUTPUT_DIR = ROOT_DIR / "Output"
BYDATE_DIR = OUTPUT_DIR / "Domain_ByDate"
BYDATE_CLEAN_DIR = OUTPUT_DIR / "Domain_ByDate_Cleaned"
FULL_REPORT_DIR = OUTPUT_DIR / "Full_Cleaned_Report"
SCREENSHOT_DIR = OUTPUT_DIR / "Screenshots"
PATTERNS_DIR = ROOT_DIR / "Patterns"
WHITELIST_DIR = ROOT_DIR / "Whitelist"

# Files
IGNORE_FILE = WHITELIST_DIR / "IgnoreDomains.txt"
INCLUDE_FILE = WHITELIST_DIR / "IncludedHits.txt"
FIRST_SEEN_FILE = OUTPUT_DIR / "Domain_First_Seen.csv"
FILTERED_DOMAINS_FILE = FULL_REPORT_DIR / "total_filtered_domains.txt"

# Create directories
for dir_path in [DAILY_DIR, BYDATE_DIR, BYDATE_CLEAN_DIR, FULL_REPORT_DIR, SCREENSHOT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Screenshot settings
SCREENSHOT_TIMEOUT_MS = 15000
SCREENSHOT_VIEWPORT = {"width": 1440, "height": 900}

# ============================================================================
# STEP 1: DOWNLOAD NRD LISTS (Last 7 days)
# ============================================================================

def download_nrd_lists():
    """Download NRD lists for the last 7 days from WhoisDS"""
    print("\n" + "="*60)
    print("STEP 1: DOWNLOADING NRD LISTS")
    print("="*60)
    
    base_url = "https://whoisds.com/whois-database/newly-registered-domains"
    session = requests.Session()
    session.headers.update({'User-Agent': 'NRD2-Downloader/1.0'})
    
    #Select previous day as starting point
    yesterday = datetime.now() - timedelta(days=1)
    total_domains = 0
    
    for i in range(7):
        date = (yesterday - timedelta(days=i)).strftime("%Y-%m-%d")
        file_path = DAILY_DIR / date
        
        # Skip if already exists
        if file_path.exists():
            print(f"[SKIP] {date} already downloaded")
            continue
        
        # Generate URL with base64 encoding (required by WhoisDS)
        date_zip = f"{date}.zip"
        infix = base64.b64encode(date_zip.encode()).decode()[:-1]  # Remove last char
        url = f"{base_url}/{infix}/nrd"
        
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check if it's a ZIP file (starts with PK magic bytes)
            if response.content[:2] == b'PK':
                # Extract ZIP
                zip_path = file_path.with_suffix('.zip')
                zip_path.write_bytes(response.content)
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Get first file in zip
                    names = zip_ref.namelist()
                    if names:
                        content = zip_ref.read(names[0]).decode('utf-8')
                        file_path.write_text(content, encoding='utf-8')
                        domain_count = len([l for l in content.split('\n') if l.strip()])
                        total_domains += domain_count
                        print(f"[OK] {date}: {domain_count:,} domains")
                
                zip_path.unlink()  # Clean up zip file
            else:
                # Plain text
                content = response.text
                file_path.write_text(content, encoding='utf-8')
                domain_count = len([l for l in content.split('\n') if l.strip()])
                total_domains += domain_count
                print(f"[OK] {date}: {domain_count:,} domains")
                
        except Exception as e:
            print(f"[ERROR] {date}: {e}")
    
    print(f"\nTotal domains downloaded: {total_domains:,}")
    
    # Download from SANS API Endpoint
    print("\n" + "="*60)
    print("DOWNLOADING FROM SANS ISC ENDPOINT")
    print("="*60)
    
    sans_total = 0
    for i in range(7):
        date = (yesterday - timedelta(days=i)).strftime("%Y-%m-%d")
        sans_file = DAILY_DIR / f"sans_{date}.json"
        
        # Skip if already exists
        if sans_file.exists():
            print(f"[SKIP] SANS {date} already downloaded")
            continue
        
        # Build SANS URL - today uses domaindata.json.gz, past dates use domaindata.YYYY-MM-DD.json.gz
        if i == 0:
            sans_url = "https://isc.sans.edu/feeds/domaindata.json.gz"
        else:
            sans_url = f"https://isc.sans.edu/feeds/domaindata.{date}.json.gz"
        
        try:
            response = session.get(sans_url, timeout=30)
            response.raise_for_status()
            
            # Decompress gzip content
            import gzip
            json_content = gzip.decompress(response.content).decode('utf-8')
            
            # Parse JSON and extract domain names
            import json
            domains_data = json.loads(json_content)
            
            # Extract just the domain names from the JSON array
            domain_names = [entry.get('domainname', '').strip() for entry in domains_data if entry.get('domainname')]
            
            # Save as plain text file (one domain per line) for consistency with WhoisDS format
            sans_file.write_text('\n'.join(domain_names), encoding='utf-8')
            
            sans_total += len(domain_names)
            print(f"[OK] SANS {date}: {len(domain_names):,} domains")
            
        except Exception as e:
            print(f"[ERROR] SANS {date}: {e}")
    
    print(f"\nTotal SANS domains downloaded: {sans_total:,}")
    print(f"Grand total domains: {total_domains + sans_total:,}")

# ============================================================================
# STEP 2: PARSE & FILTER DOMAINS
# ============================================================================

def load_patterns(pattern_file: Path) -> List[re.Pattern]:
    """Load regex patterns from file"""
    patterns = []
    if pattern_file.exists():
        with open(pattern_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(re.compile(re.escape(line), re.IGNORECASE))
    return patterns

def normalize_domain(domain: str) -> str:
    """Normalize domain for comparison"""
    d = domain.strip().lower()
    if "://" in d:
        d = d.split("://", 1)[1]
    if "/" in d:
        d = d.split("/", 1)[0]
    if d.startswith("www."):
        d = d[4:]
    return d.rstrip('.')

def load_first_seen_map() -> Dict[str, str]:
    """Load first_seen tracking"""
    first_seen = {}
    if FIRST_SEEN_FILE.exists():
        with open(FIRST_SEEN_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                domain = row.get('domain', '').strip()
                date = row.get('first_seen', '').strip()
                if domain and date:
                    first_seen[domain.lower()] = date
    return first_seen

def save_first_seen_map(first_seen: Dict[str, str]):
    """Save first_seen tracking"""
    with open(FIRST_SEEN_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['domain', 'first_seen'])
        for domain in sorted(first_seen.keys()):
            writer.writerow([domain, first_seen[domain]])

def load_whitelist_set(file_path: Path) -> Set[str]:
    """Load whitelist/ignore domains"""
    domains = set()
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    domains.add(normalize_domain(line))
    return domains

def strict_filter_domains(domains, ignore_set: set[str]):
    strict_patterns = [
    re.compile(r"^absa.*", re.IGNORECASE),     # starts with absa
    re.compile(r".*absa$", re.IGNORECASE),     # ends with absa
    ]


    filtered = []
    for domain in domains:
        norm = normalize_domain(domain)
        if norm in ignore_set:
            continue
        if any(pat.match(domain) for pat in strict_patterns):
            filtered.append(domain)
    return filtered

def parse_and_filter_domains():
    """Parse raw NRD files and filter for relevant domains"""
    print("\n" + "="*60)
    print("STEP 2: PARSING & FILTERING DOMAINS")
    print("="*60)
    
    # Load patterns
    typo_patterns = load_patterns(PATTERNS_DIR / "typos.txt")
    presuf_patterns = load_patterns(PATTERNS_DIR / "presuf.txt")
    tld_patterns = load_patterns(PATTERNS_DIR / "TLD.txt")
    keyword_patterns = load_patterns(PATTERNS_DIR / "keywords.txt")
    
    # Combine all patterns
    all_patterns = typo_patterns + presuf_patterns + tld_patterns + keyword_patterns
    
    # Static patterns
    pattern_coza = re.compile(r"\.co\.za$", re.IGNORECASE)
    pattern_africa = re.compile(r"\.africa$", re.IGNORECASE)
    pattern_absa = re.compile(r"absa", re.IGNORECASE)
    
    # Load whitelists
    ignore_set = load_whitelist_set(IGNORE_FILE)
    include_set = load_whitelist_set(INCLUDE_FILE)
    
    # Load first_seen tracking
    first_seen_map = load_first_seen_map()
    
    # Track all filtered domains
    all_filtered_domains = []
    
    # Process each daily file
    for file_path in sorted(DAILY_DIR.iterdir()):
        if not file_path.is_file():
            continue
        
        # Extract date from filename
        filename = file_path.name
        
        # Handle SANS files (sans_YYYY-MM-DD.json) and WhoisDS files (YYYY-MM-DD)
        is_sans = filename.startswith('sans_') and filename.endswith('.json')
        if is_sans:
            date_str = filename[5:-5]  # Remove 'sans_' prefix and '.json' suffix
            source = 'SANS'
        else:
            date_str = filename  # YYYY-MM-DD format (no extension)
            source = 'WhoisDS'
        
        # Skip if already processed - use different output names for SANS vs WhoisDS
        if is_sans:
            bydate_output = BYDATE_DIR / f"{date_str}_Sans.txt"
            clean_output = BYDATE_CLEAN_DIR / f"{date_str}_Sans.txt"
        else:
            bydate_output = BYDATE_DIR / f"{date_str}.txt"
            clean_output = BYDATE_CLEAN_DIR / f"{date_str}.txt"
        
        if bydate_output.exists():
            #print(f"[SKIP] {source} {date_str} already parsed")
            continue
        
        print(f"\n[PROCESSING] {date_str} ({source})")
        
        # Read domains
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            domains = [line.strip() for line in f if line.strip()]
        
        # Categorize domains
        golden_matches = []
        coza_only = []
        absa_only = []
        africa_only = []
        pattern_matches = []
        
        for domain in domains:
            # Check if ignored
            if normalize_domain(domain) in ignore_set:
                continue
            
            has_coza = bool(pattern_coza.search(domain))
            has_africa = bool(pattern_africa.search(domain))
            has_absa = bool(pattern_absa.search(domain))
            
            # Golden match: (.co.za OR .africa) AND absa
            if (has_coza or has_africa) and has_absa:
                golden_matches.append(domain)
            elif has_coza:
                coza_only.append(domain)
            elif has_absa:
                absa_only.append(domain)
            elif has_africa:
                africa_only.append(domain)
            
            # Check pattern matches
            if any(p.search(domain) for p in all_patterns):
                pattern_matches.append(domain)
        
        # Combine all matches (deduplicate)
        all_matches = list(dict.fromkeys(
            golden_matches + coza_only + absa_only + pattern_matches + africa_only
        ))
        
        # Update the first seen map to accurately show the dates
        for domain in all_matches:
            domain_lower = domain.lower()
            if domain_lower not in first_seen_map:
                first_seen_map[domain_lower] = date_str
        
        # Write categorized output
        with open(bydate_output, 'w', encoding='utf-8') as f:
            f.write(f"Summary for {date_str}:\n")
            f.write(f"  - Golden Matches: {len(golden_matches)}\n")
            f.write(f"  - .co.za Only: {len(coza_only)}\n")
            f.write(f"  - absa Only: {len(absa_only)}\n")
            f.write(f"  - Pattern Matches: {len(pattern_matches)}\n")
            f.write(f"  - .africa Only: {len(africa_only)}\n")
            f.write(f"  - Total: {len(all_matches)}\n")
            f.write("=" * 40 + "\n\n")
            
            f.write("=== Golden Matches ===\n")
            f.write("\n".join(golden_matches) + "\n\n")
            
            f.write("=== absa Only ===\n")
            f.write("\n".join(absa_only) + "\n\n")

            f.write("=== Other Matches ===\n")
            f.write("--------------------------------------------------------------------------\n")
            f.write("=== .co.za Only ===\n")
            f.write("\n".join(coza_only) + "\n\n")
                
            f.write("=== Pattern Matches ===\n")
            f.write("\n".join(pattern_matches) + "\n\n")
            
            f.write("=== .africa Only ===\n")
            f.write("\n".join(africa_only) + "\n")
        
        # Write clean filtered list (already defined above based on is_sans)
        with open(clean_output, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_matches))
        
        all_filtered_domains.extend(all_matches)

       
        
        print(f"  Total matched: {len(all_matches)}")
    
    #Filter with strict rules
    all_filtered_domains = strict_filter_domains(all_filtered_domains, ignore_set)

    #sanity check the all filtered domains, print all domains
    for domain in all_filtered_domains:
        print(f"[FILTERED DOMAIN] {domain}")
    print(f"\n[INFO] Total filtered domains before include and deduplication: {len(all_filtered_domains)}")


    # Merge with include list and deduplicate
    merged_domains = list(dict.fromkeys(all_filtered_domains + list(include_set)))
    
    
    # Write total filtered domains
    # with open(FILTERED_DOMAINS_FILE, 'w', encoding='utf-8') as f:
    #     f.write("\n".join(sorted(merged_domains)))
    
    # Append to the domains files, ensuring no deletions
    with open(FILTERED_DOMAINS_FILE, 'a', encoding='utf-8') as f:
        for domain in sorted(merged_domains):
            f.write(domain + "\n")

    # Save first_seen tracking
    save_first_seen_map(first_seen_map)
    
    print(f"\n[OK] Total unique filtered domains: {len(merged_domains)}")
    print(f"[OK] First seen tracking: {len(first_seen_map)} domains")

# ============================================================================
# STEP 3: SCAN DOMAINS FOR ACTIVITY
# ============================================================================

async def scan_single_domain(domain: str, domain_data: dict, first_seen_map: dict, db) -> dict:
    """Scan a single domain for activity and content changes"""
    # Fetch domain content
    is_active = False
    content_hash = None
    
    for url in [f"https://{domain}", f"http://{domain}"]:
        try:
            loop = asyncio.get_event_loop()
            # Use asyncio to run requests in thread pool
            r = await loop.run_in_executor(
                None, 
                lambda: requests.get(url, timeout=5)
            )
            if r.status_code == 200 and r.text.strip():
                is_active = True
                content_hash = hashlib.md5(r.text.encode('utf-8')).hexdigest()
                break
        except:
            continue
    
    # Check if content changed
    prev_data = domain_data.get(domain, {})
    prev_hash = prev_data.get('content_hash')
    changed = bool(content_hash and prev_hash and prev_hash != content_hash)
    
    # Get first_seen
    first_seen_raw = first_seen_map.get(domain.lower()) or prev_data.get('first_seen')
    
    # Convert first_seen to ISO timestamp if it's just a date string
    if first_seen_raw:
        try:
            # If it's already an ISO timestamp, keep it
            if 'T' in first_seen_raw:
                first_seen = first_seen_raw
            else:
                # Convert date string (YYYY-MM-DD) to ISO timestamp
                first_seen = datetime.strptime(first_seen_raw, '%Y-%m-%d').replace(tzinfo=timezone.utc).isoformat()
        except:
            # If parsing fails, use current time
            first_seen = datetime.now(timezone.utc).isoformat()
    else:
        first_seen = datetime.now(timezone.utc).isoformat()
    
    # Get category and tags for the domain
    category = prev_data.get('category', 'unknown')
    tags = prev_data.get('tags', [])
    
    # Update database
    checked_at = datetime.now(timezone.utc).isoformat()
    domain_id = await db.upsert_domain(
        domain=domain,
        first_seen=first_seen,
        last_checked=checked_at,
        is_active=is_active,
        content_hash=content_hash or "",
        content_changed=changed,
        has_profile=prev_data.get('has_profile', False),
        category=category,
        tags=tags
    )
    
    # Add history
    await db.add_history_entry(
        domain_id=domain_id,
        checked_at=checked_at,
        is_active=is_active,
        content_hash=content_hash,
        content_changed=changed
    )
    
    return {
        'domain': domain,
        'is_active': is_active,
        'changed': changed
    }


async def scan_domains():
    """Scan filtered domains for activity and content changes with parallel processing"""
    print("\n" + "="*60)
    print("STEP 3: SCANNING DOMAINS (PARALLEL MODE)")
    print("="*60)
    
    # Initialize database
    db = get_db()
    
    # Load filtered domains
    if not FILTERED_DOMAINS_FILE.exists():
        print("[ERROR] No filtered domains file found")
        return
    
    with open(FILTERED_DOMAINS_FILE, 'r', encoding='utf-8') as f:
        domains = [line.strip() for line in f if line.strip()]
    
    # Load ignore list
    ignore_set = load_whitelist_set(IGNORE_FILE)
    domains = [d for d in domains if normalize_domain(d) not in ignore_set]
    
    print(f"[*] Scanning {len(domains)} domains")
    
    # Get existing domain data from database
    existing_domains = await db.get_all_domains()
    domain_data = {d['domain']: d for d in existing_domains}
    
    # Prioritize: active first, then unknown, then inactive
    active_domains = [d for d in domains if d in domain_data and domain_data[d]['is_active']]
    unknown_domains = [d for d in domains if d not in domain_data]
    inactive_domains = [d for d in domains if d in domain_data and not domain_data[d]['is_active']]
    
    prioritized = active_domains + unknown_domains + inactive_domains
    
    print(f"  - Active: {len(active_domains)}")
    print(f"  - Unknown: {len(unknown_domains)}")
    print(f"  - Inactive: {len(inactive_domains)}")
    
    # Load first_seen map once
    first_seen_map = load_first_seen_map()
    
    # Scan domains in parallel batches
    active_count = 0
    changed_count = 0
    max_concurrent = 10  # Adjust based on system resources and rate limits
    
    for i in range(0, len(prioritized), max_concurrent):
        batch = prioritized[i:i + max_concurrent]
        
        # Scan batch concurrently
        tasks = [
            scan_single_domain(domain, domain_data, first_seen_map, db)
            for domain in batch
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count results
        for result in results:
            if isinstance(result, dict):
                if result.get('is_active'):
                    active_count += 1
                if result.get('changed'):
                    changed_count += 1
        
        # Progress update
        processed = min(i + max_concurrent, len(prioritized))
        print(f"  Progress: {processed}/{len(prioritized)} | Active: {active_count} | Changed: {changed_count}")
    
    print(f"\n[OK] Scan complete: {active_count} active, {changed_count} changed")

# ============================================================================
# STEP 4: CAPTURE SCREENSHOTS
# ============================================================================

async def capture_screenshots():
    """Capture screenshots of active domains using hybrid approach"""
    print("\n" + "="*60)
    print("STEP 4: CAPTURING SCREENSHOTS (HYBRID MODE)")
    print("="*60)
    
    if not SCREENSHOT_AVAILABLE:
        print("[SKIP] Screenshot modules not available")
        return
    
    # Get active domains from database
    db = get_db()
    all_domains = await db.get_all_domains()
    active_domains = [d for d in all_domains if d['is_active']]
    
    print(f"[*] Found {len(active_domains)} active domains")
    
    # Load screenshot index
    index_file = SCREENSHOT_DIR / "index.json"
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
    else:
        index = {"domains": {}}
    
    # Filter domains that need screenshots (content changed or new)
    domains_to_capture = []
    skipped_count = 0
    
    for domain_data in active_domains:
        domain = domain_data['domain']
        content_hash = domain_data['content_hash']
        
        # Check if we should capture
        domain_meta = index['domains'].get(domain, {})
        last_hash = domain_meta.get('last_content_hash', '')
        
        # Skip if content hasn't changed
        if content_hash and last_hash == content_hash:
            skipped_count += 1
            continue
        
        domains_to_capture.append({
            'domain': domain,
            'url': f"https://{domain}",
            'content_hash': content_hash
        })
    
    if not domains_to_capture:
        print(f"[OK] No new screenshots needed ({skipped_count} domains unchanged)")
        return
    
    print(f"[*] Capturing {len(domains_to_capture)} screenshots ({skipped_count} skipped)")
    
    # Initialize hybrid screenshot capturer
    capturer = HybridScreenshotCapture(
        output_dir=str(SCREENSHOT_DIR),
        max_concurrent=3  # Optimized for t3.small (2GB RAM)
    )
    
    # Capture screenshots in parallel batches
    results = await capturer.capture_batch_parallel(domains_to_capture)
    
    # Update index with results
    captured_count = 0
    for result in results:
        if result.get('success'):
            domain = result['domain']
            content_hash = result.get('content_hash')
            ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            
            index['domains'][domain] = {
                'last_content_hash': content_hash,
                'last_screenshot': ts,
                'last_screenshot_path': str(Path('Output/Screenshots') / result['filename']),
                'capture_method': result.get('method', 'unknown')
            }
            captured_count += 1
            print(f"[OK] {domain}: screenshot saved ({result.get('method', 'unknown')})")
    
    # Save index
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)
    
    print(f"\n[OK] Screenshots complete: {captured_count} captured, {skipped_count} skipped")

# ============================================================================
# MAIN WORKFLOW
# ============================================================================

async def main():
    """Execute the complete NRD2 workflow"""
    print("\n" + "="*60)
    print("NRD2 WORKFLOW - MINIMAL PIPELINE")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    
    try:
        # Step 1: Download NRD lists
        download_nrd_lists()
        
        # Step 2: Parse and filter domains
        parse_and_filter_domains()
        
        # Step 3: Scan domains for activity
        await scan_domains()
        
        # Step 4: Capture screenshots
        await capture_screenshots()
        
        # Done
        elapsed = time.time() - start_time
        print("\n" + "="*60)
        print("WORKFLOW COMPLETE")
        print("="*60)
        print(f"Total time: {elapsed/60:.1f} minutes")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n\n[!] Workflow interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Workflow failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
