#!/usr/bin/env python3
"""
Populate database with real domain data from total_filtered_domains.txt
Categorizes domains and assigns tags based on pattern matching
"""
import asyncio
import sys
import re
import csv
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Set

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from db_manager import get_db

# ============================================================================
# CONFIGURATION
# ============================================================================

ROOT_DIR = Path(__file__).parent.absolute()
OUTPUT_DIR = ROOT_DIR / "Output"
FULL_REPORT_DIR = OUTPUT_DIR / "Full_Cleaned_Report"
PATTERNS_DIR = ROOT_DIR / "Patterns"

# Files
FILTERED_DOMAINS_FILE = FULL_REPORT_DIR / "total_filtered_domains.txt"
FIRST_SEEN_FILE = OUTPUT_DIR / "Domain_First_Seen.csv"

# ============================================================================
# PATTERN LOADING
# ============================================================================

def load_patterns(pattern_file: Path) -> List[re.Pattern]:
    """Load regex patterns from file"""
    patterns = []
    if pattern_file.exists():
        with open(pattern_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        patterns.append(re.compile(line, re.IGNORECASE))
                    except re.error as e:
                        print(f"[!] Invalid regex pattern '{line}': {e}")
    return patterns

def load_first_seen_map() -> Dict[str, str]:
    """Load first_seen tracking from CSV"""
    first_seen = {}
    if FIRST_SEEN_FILE.exists():
        with open(FIRST_SEEN_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                domain = row['domain'].strip().lower()
                # Convert "2025-03-03.txt" to ISO date "2025-03-03T00:00:00Z"
                date_str = row['first_seen'].replace('.txt', '')
                try:
                    # Parse and convert to ISO format
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                    iso_date = dt.replace(tzinfo=timezone.utc).isoformat()
                    first_seen[domain] = iso_date
                except ValueError:
                    # If parsing fails, use as-is
                    first_seen[domain] = date_str
    return first_seen

# ============================================================================
# DOMAIN CATEGORIZATION
# ============================================================================

def categorize_domain(domain: str, patterns_dict: dict) -> dict:
    """
    Categorize domain with primary category and secondary tags
    
    Returns:
        {
            'category': str,  # golden, absa, coza, africa, pattern
            'tags': [str]     # typo, presuf, keyword, etc.
        }
    """
    domain_lower = domain.lower()
    
    # Check base TLD patterns
    has_coza = domain_lower.endswith('.co.za')
    has_africa = domain_lower.endswith('.africa')
    has_absa = 'absa' in domain_lower
    
    # Determine primary category (priority order)
    if has_coza and has_absa:
        primary = 'golden'
    elif has_africa and has_absa:
        primary = 'golden'
    elif has_absa:
        primary = 'absa'
    elif has_coza:
        primary = 'coza'
    elif has_africa:
        primary = 'africa'
    else:
        primary = 'pattern'
    
    # Determine secondary tags (what patterns matched)
    tags = []
    
    # Check typo patterns
    if any(p.match(domain) for p in patterns_dict.get('typos', [])):
        tags.append('typo')
    
    # Check prefix/suffix patterns
    if any(p.match(domain) for p in patterns_dict.get('presuf', [])):
        tags.append('presuf')
    
    # Check keyword patterns
    if any(p.match(domain) for p in patterns_dict.get('keywords', [])):
        tags.append('keyword')
    
    # Check TLD patterns (beyond .co.za and .africa)
    if any(p.match(domain) for p in patterns_dict.get('tld', [])):
        tags.append('tld-match')
    
    # Add domain structure tags
    if has_absa:
        if domain_lower.startswith('absa'):
            tags.append('starts-with-absa')
        if domain_lower.endswith('absa'):
            tags.append('ends-with-absa')
        if 'absa' in domain_lower[1:-4]:  # Absa in middle
            tags.append('contains-absa')
    
    return {
        'category': primary,
        'tags': tags
    }

# ============================================================================
# MAIN POPULATION LOGIC
# ============================================================================

async def populate_database():
    """Populate database with real domain data"""
    print("\n" + "="*80)
    print("POPULATING DATABASE WITH REAL DOMAIN DATA")
    print("="*80)
    
    # Initialize database
    db = get_db()
    await db._ensure_indexes()
    
    # Load pattern files
    print("\n[1/5] Loading pattern files...")
    patterns_dict = {
        'typos': load_patterns(PATTERNS_DIR / "typos.txt"),
        'presuf': load_patterns(PATTERNS_DIR / "presuf.txt"),
        'tld': load_patterns(PATTERNS_DIR / "TLD.txt"),
        'keywords': load_patterns(PATTERNS_DIR / "keywords.txt"),
    }
    
    print(f"  ✓ Loaded {len(patterns_dict['typos'])} typo patterns")
    print(f"  ✓ Loaded {len(patterns_dict['presuf'])} prefix/suffix patterns")
    print(f"  ✓ Loaded {len(patterns_dict['tld'])} TLD patterns")
    print(f"  ✓ Loaded {len(patterns_dict['keywords'])} keyword patterns")
    
    # Load first_seen data
    print("\n[2/5] Loading first seen dates...")
    first_seen_map = load_first_seen_map()
    print(f"  ✓ Loaded {len(first_seen_map)} first seen dates")
    
    # Load filtered domains
    print("\n[3/5] Loading filtered domains...")
    if not FILTERED_DOMAINS_FILE.exists():
        print(f"  [ERROR] File not found: {FILTERED_DOMAINS_FILE}")
        return
    
    with open(FILTERED_DOMAINS_FILE, 'r', encoding='utf-8') as f:
        domains = [line.strip() for line in f if line.strip()]
    
    print(f"  ✓ Loaded {len(domains)} domains")
    
    # Clear existing data
    print("\n[4/5] Clearing existing database...")
    response = input("  ⚠️  This will DELETE ALL existing domains. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("  [CANCELLED] Database population cancelled")
        return
    
    await db.domains.delete_many({})
    await db.history.delete_many({})
    print("  ✓ Database cleared")
    
    # Populate database
    print("\n[5/5] Populating database...")
    print("-" * 80)
    
    category_counts = {}
    tag_counts = {}
    
    for i, domain in enumerate(domains, 1):
        # Categorize domain
        categorization = categorize_domain(domain, patterns_dict)
        category = categorization['category']
        tags = categorization['tags']
        
        # Get first_seen date
        domain_lower = domain.lower()
        first_seen = first_seen_map.get(domain_lower)
        if not first_seen:
            # Use current date if not found
            first_seen = datetime.now(timezone.utc).isoformat()
        
        # Insert domain (initially inactive, to be scanned)
        domain_id = await db.upsert_domain(
            domain=domain,
            first_seen=first_seen,
            last_checked=None,
            is_active=False,
            content_hash="",
            content_changed=False,
            has_profile=False,
            tags=tags,
            notes=None,
            category=category
        )
        
        # Track statistics
        category_counts[category] = category_counts.get(category, 0) + 1
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Progress indicator
        if i % 10 == 0 or i == len(domains):
            print(f"  [{i}/{len(domains)}] Processed: {domain} -> {category} {tags}")
    
    print("-" * 80)
    print("\n✅ DATABASE POPULATION COMPLETE")
    
    # Print statistics
    print("\n" + "="*80)
    print("STATISTICS")
    print("="*80)
    
    stats = await db.get_stats()
    print(f"\n📊 Domain Counts:")
    print(f"  Total:         {stats['total']}")
    print(f"  Active:        {stats['active']}")
    print(f"  Inactive:      {stats['inactive']}")
    
    print(f"\n🏷️  Categories:")
    for cat in ['golden', 'absa', 'coza', 'africa', 'pattern']:
        count = category_counts.get(cat, 0)
        pct = (count / len(domains) * 100) if domains else 0
        print(f"  {cat.ljust(10)} {count:>4} ({pct:>5.1f}%)")
    
    print(f"\n🔖 Tags:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(domains) * 100) if domains else 0
        print(f"  {tag.ljust(20)} {count:>4} ({pct:>5.1f}%)")
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. Run domain scanning:    python main.py (or run scan_domains() function)")
    print("2. Run screenshot capture: python main.py (or run capture_screenshots() function)")
    print("3. Start backend server:   cd backend && python server.py")
    print("4. Start frontend:         cd frontend && npm start")
    print("="*80)

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        asyncio.run(populate_database())
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
