#!/usr/bin/env python3
"""
Seed script to add sample domains to the database
"""
import asyncio
from datetime import datetime, timezone, timedelta
import random
from backend.db_manager import get_db

# Sample domains
SAMPLE_DOMAINS = [
    # Golden matches (.co.za + absa)
    {"domain": "absa-online.co.za", "category": "golden", "is_active": True, "tags": ["starts-with-absa"]},
    {"domain": "secure-absa.co.za", "category": "golden", "is_active": True, "tags": ["contains-absa"]},
    {"domain": "login-absa.co.za", "category": "golden", "is_active": False, "tags": ["contains-absa"]},
    
    # .africa + absa
    {"domain": "absa-bank.africa", "category": "golden", "is_active": True, "tags": ["starts-with-absa"]},
    {"domain": "myabsa.africa", "category": "golden", "is_active": True, "tags": ["starts-with-absa"]},
    
    # .co.za only
    {"domain": "financeportal.co.za", "category": "coza", "is_active": True, "tags": []},
    {"domain": "bankingonline.co.za", "category": "coza", "is_active": False, "tags": []},
    {"domain": "securebank.co.za", "category": "coza", "is_active": True, "tags": []},
    
    # absa only (other TLDs)
    {"domain": "absa-verify.com", "category": "absa", "is_active": True, "tags": ["starts-with-absa"]},
    {"domain": "absaonline.net", "category": "absa", "is_active": True, "tags": ["starts-with-absa"]},
    {"domain": "myabsa-account.org", "category": "absa", "is_active": False, "tags": ["starts-with-absa"]},
    
    # Pattern matches
    {"domain": "account-absa.com", "category": "pattern", "is_active": True, "tags": ["ends-with-absa", "presuf"]},
    {"domain": "loginabsa.net", "category": "pattern", "is_active": True, "tags": ["ends-with-absa", "presuf"]},
    {"domain": "absa-portal.info", "category": "pattern", "is_active": False, "tags": ["starts-with-absa", "presuf"]},
    
    # More samples
    {"domain": "absabanking.online", "category": "absa", "is_active": True, "tags": ["starts-with-absa"]},
    {"domain": "secure-banking.co.za", "category": "coza", "is_active": True, "tags": []},
    {"domain": "absa-support.com", "category": "absa", "is_active": False, "tags": ["starts-with-absa"]},
    {"domain": "verifyabsa.net", "category": "pattern", "is_active": True, "tags": ["ends-with-absa"]},
    {"domain": "absa-update.co.za", "category": "golden", "is_active": True, "tags": ["starts-with-absa"]},
    {"domain": "mobile-absa.africa", "category": "golden", "is_active": True, "tags": ["contains-absa"]},
]

async def seed_database():
    """Seed the database with sample domains"""
    db = get_db()
    
    print("🌱 Seeding database with sample domains...")
    print("=" * 60)
    
    # Ensure tables
    await db._ensure_tables()
    
    # Clear existing data (optional)
    # await db.domains.delete_many({})
    # await db.history.delete_many({})
    # print("✓ Cleared existing data")
    
    # Add sample domains
    for i, domain_data in enumerate(SAMPLE_DOMAINS, 1):
        # Random first_seen date (last 30 days)
        days_ago = random.randint(1, 30)
        first_seen = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
        
        # Random last_checked (within last 24 hours)
        hours_ago = random.randint(1, 24)
        last_checked = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
        
        # Random content hash
        content_hash = f"{'abcd1234' * 4}{str(random.randint(1000, 9999))}"
        
        # Some domains have content changed
        content_changed = random.choice([True, False]) if domain_data["is_active"] else False
        
        # Random has_profile
        has_profile = random.choice([True, False]) if domain_data["category"] == "golden" else False
        
        # Add notes for golden category domains
        notes = None
        if domain_data["category"] == "golden":
            notes = f"Golden match domain detected. Category: {domain_data['category']}. Requires immediate investigation."
        
        # Get tags from domain data
        tags = domain_data.get("tags", [])
        
        # Insert domain
        domain_id = await db.upsert_domain(
            domain=domain_data["domain"],
            first_seen=first_seen,
            last_checked=last_checked,
            is_active=domain_data["is_active"],
            content_hash=content_hash if domain_data["is_active"] else "",
            content_changed=content_changed,
            has_profile=has_profile,
            tags=tags,
            notes=notes,
            category=domain_data["category"]
        )
        
        # Add some history entries
        num_history = random.randint(2, 8)
        for j in range(num_history):
            history_days_ago = days_ago - random.randint(0, min(5, days_ago))
            history_checked = (datetime.now(timezone.utc) - timedelta(days=history_days_ago, hours=random.randint(0, 23))).isoformat()
            
            await db.add_history_entry(
                domain_id=domain_id,
                checked_at=history_checked,
                is_active=random.choice([True, False, domain_data["is_active"]]),
                content_hash=content_hash if random.choice([True, False]) else None,
                content_changed=random.choice([True, False]),
                screenshot_taken=random.choice([True, False]) if domain_data["is_active"] else False
            )
        
        print(f"✓ Added: {domain_data['domain']} ({domain_data['category']}, tags: {tags})")
    
    print("=" * 60)
    print(f"✅ Successfully seeded {len(SAMPLE_DOMAINS)} domains")
    
    # Print stats
    stats = await db.get_stats()
    print("\n📊 Database Statistics:")
    print(f"  Total: {stats['total']}")
    print(f"  Active: {stats['active']}")
    print(f"  Inactive: {stats['inactive']}")
    print(f"  Golden Matches: {stats['golden_matches']}")
    print(f"  Category - Golden: {stats.get('category_golden', 0)}")
    print(f"  Category - ABSA: {stats.get('category_absa', 0)}")
    print(f"  Category - CO.ZA: {stats.get('category_coza', 0)}")
    print(f"  Category - Africa: {stats.get('category_africa', 0)}")
    print(f"  Category - Pattern: {stats.get('category_pattern', 0)}")

if __name__ == "__main__":
    asyncio.run(seed_database())
