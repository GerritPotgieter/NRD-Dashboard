#!/usr/bin/env python3
"""
Migration script to add risk_level field to existing domain documents
"""
import sys
import asyncio
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from db_manager import get_db

async def migrate_risk_levels():
    """Add risk_level field to all existing domains without it"""
    print("Starting risk_level migration...")
    
    db = get_db()
    
    # Update all documents that don't have risk_level
    result = await db.domains.update_many(
        {"risk_level": {"$exists": False}},  # Only update documents without risk_level
        {"$set": {"risk_level": "unknown"}}
    )
    
    print(f"✅ Updated {result.modified_count} domains with default risk_level='unknown'")
    
    # Get total count for verification
    total = await db.domains.count_documents({})
    with_risk_level = await db.domains.count_documents({"risk_level": {"$exists": True}})
    
    print(f"📊 Total domains: {total}")
    print(f"📊 Domains with risk_level: {with_risk_level}")
    print("✅ Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate_risk_levels())
