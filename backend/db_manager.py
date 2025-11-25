import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import uuid

# === Path Setup ===
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / "backend" / '.env')

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'nrd_monitoring')

# Initialize MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections
domains_collection = db['domains']
domain_history_collection = db['domain_history']


class DomainDB:
    """Database manager for domain tracking - MongoDB version"""
    
    def __init__(self):
        """Initialize database connection"""
        self.domains = domains_collection
        self.history = domain_history_collection
    
    async def _ensure_indexes(self):
        """Create indexes for performance"""
        # Domain indexes
        await self.domains.create_index("domain", unique=True)
        await self.domains.create_index("is_active")
        await self.domains.create_index("first_seen")
        await self.domains.create_index("last_checked")
        await self.domains.create_index("content_changed")
        
        # History indexes
        await self.history.create_index("domain_id")
        await self.history.create_index("checked_at")
    
    async def upsert_domain(self, domain: str, first_seen: Optional[str] = None,
                     last_checked: Optional[str] = None, is_active: bool = False,
                     content_hash: Optional[str] = None, content_changed: bool = False,
                     has_profile: bool = False, tags: Optional[List[str]] = None,
                     notes: Optional[str] = None, category: Optional[str] = None,
                     risk_level: Optional[str] = None) -> str:
        """
        Insert or update a domain record
        Returns the domain_id (UUID)
        """
        now = datetime.now(timezone.utc).isoformat()
        last_checked = last_checked or now
        first_seen = first_seen or now
        tags = tags or []
        risk_level = risk_level or 'unknown'
        
        # Check if domain exists
        existing = await self.domains.find_one({"domain": domain})
        
        if existing:
            # Update existing domain
            domain_id = existing['id']
            update_data = {
                "last_checked": last_checked,
                "is_active": is_active,
                "content_hash": content_hash or "",
                "content_changed": content_changed,
                "has_profile": has_profile,
                "tags": tags,
                "notes": notes,
                "category": category,
                "updated_at": now
            }
            # Only update risk_level if it's explicitly provided or doesn't exist
            if risk_level or 'risk_level' not in existing:
                update_data['risk_level'] = risk_level
            
            await self.domains.update_one(
                {"domain": domain},
                {"$set": update_data}
            )
        else:
            # Insert new domain with risk_level
            domain_id = str(uuid.uuid4())
            await self.domains.insert_one({
                "id": domain_id,
                "domain": domain,
                "first_seen": first_seen,
                "last_checked": last_checked,
                "is_active": is_active,
                "content_hash": content_hash or "",
                "content_changed": content_changed,
                "has_profile": has_profile,
                "tags": tags,
                "notes": notes,
                "category": category,
                "risk_level": risk_level,
                "created_at": now,
                "updated_at": now
            })
        
        return domain_id
    
    async def add_history_entry(self, domain_id: str, checked_at: Optional[str] = None,
                         is_active: bool = False, content_hash: Optional[str] = None,
                         content_changed: bool = False, screenshot_taken: bool = False):
        """Add a history entry for a domain scan"""
        checked_at = checked_at or datetime.now(timezone.utc).isoformat()
        
        history_id = str(uuid.uuid4())
        await self.history.insert_one({
            "id": history_id,
            "domain_id": domain_id,
            "checked_at": checked_at,
            "is_active": is_active,
            "content_hash": content_hash,
            "content_changed": content_changed,
            "screenshot_taken": screenshot_taken
        })
    
    async def get_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get a single domain by name"""
        result = await self.domains.find_one({"domain": domain}, {"_id": 0})
        if result:
            # Ensure risk_level has a default value for existing documents
            result.setdefault('risk_level', 'unknown')
            result.setdefault('tags', [])
            result.setdefault('notes', '')
        return result
    
    async def get_domain_by_id(self, domain_id: str) -> Optional[Dict[str, Any]]:
        """Get a single domain by ID"""
        result = await self.domains.find_one({"id": domain_id}, {"_id": 0})
        if result:
            # Ensure risk_level has a default value for existing documents
            result.setdefault('risk_level', 'unknown')
            result.setdefault('tags', [])
            result.setdefault('notes', '')
        return result
    
    async def get_all_domains(self, active_only: bool = False, 
                       changed_only: bool = False,
                       with_profile_only: bool = False,
                       category: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       search_term: Optional[str] = None,
                       limit: Optional[int] = None,
                       offset: int = 0,
                       sort_by: str = "last_checked",
                       sort_order: int = -1) -> List[Dict[str, Any]]:
        """Get all domains with optional filters"""
        query = {}
        
        if active_only:
            query["is_active"] = True
        
        if changed_only:
            query["content_changed"] = True
        
        if with_profile_only:
            query["has_profile"] = True
        
        if category:
            query["category"] = category
        
        if tags:
            query["tags"] = {"$in": tags}
        
        if search_term:
            query["domain"] = {"$regex": search_term, "$options": "i"}
        
        cursor = self.domains.find(query, {"_id": 0}).sort(sort_by, sort_order).skip(offset)
        
        if limit:
            cursor = cursor.limit(limit)
        
        results = await cursor.to_list(length=None)
        
        # Ensure risk_level has a default value for existing documents
        for result in results:
            result.setdefault('risk_level', 'unknown')
            result.setdefault('tags', [])
            result.setdefault('notes', '')
        
        return results
    
    async def get_domain_count(self, active_only: bool = False, 
                       changed_only: bool = False,
                       with_profile_only: bool = False,
                       category: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       search_term: Optional[str] = None) -> int:
        """Get count of domains with filters"""
        query = {}
        
        if active_only:
            query["is_active"] = True
        
        if changed_only:
            query["content_changed"] = True
        
        if with_profile_only:
            query["has_profile"] = True
        
        if category:
            query["category"] = category
        
        if tags:
            query["tags"] = {"$in": tags}
        
        if search_term:
            query["domain"] = {"$regex": search_term, "$options": "i"}
        
        count = await self.domains.count_documents(query)
        return count
    
    async def get_domain_history(self, domain: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get history entries for a domain"""
        domain_doc = await self.domains.find_one({"domain": domain})
        if not domain_doc:
            return []
        
        domain_id = domain_doc['id']
        cursor = self.history.find(
            {"domain_id": domain_id},
            {"_id": 0}
        ).sort("checked_at", -1).limit(limit)
        
        results = await cursor.to_list(length=limit)
        return results
    
    async def update_profile_status(self, domain: str, has_profile: bool):
        """Update profile existence status for a domain"""
        await self.domains.update_one(
            {"domain": domain},
            {"$set": {
                "has_profile": has_profile,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    async def update_domain_notes(self, domain: str, notes: str):
        """Update notes for a domain"""
        await self.domains.update_one(
            {"domain": domain},
            {"$set": {
                "notes": notes,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    async def update_risk_level(self, domain: str, tags: List[str]):
        """Update tags for a domain"""
        await self.domains.update_one(
            {"domain": domain},
            {"$set": {
                "tags": tags,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    async def get_stats(self) -> Dict[str, int]:
        """Get statistics about domains"""
        stats = {}
        
        # Total domains
        stats['total'] = await self.domains.count_documents({})
        
        # Active domains
        stats['active'] = await self.domains.count_documents({"is_active": True})
        
        # Inactive domains
        stats['inactive'] = await self.domains.count_documents({"is_active": False})
        
        # Changed domains
        stats['changed'] = await self.domains.count_documents({"content_changed": True})
        
        # Domains with profiles
        stats['with_profiles'] = await self.domains.count_documents({"has_profile": True})
        
        # Golden matches (contains .co.za or .africa AND absa)
        stats['golden_matches'] = await self.domains.count_documents({"category": "golden"})
        
        # By category
        stats['category_golden'] = await self.domains.count_documents({"category": "golden"})
        stats['category_absa'] = await self.domains.count_documents({"category": "absa"})
        stats['category_coza'] = await self.domains.count_documents({"category": "coza"})
        stats['category_africa'] = await self.domains.count_documents({"category": "africa"})
        stats['category_pattern'] = await self.domains.count_documents({"category": "pattern"})
        
        return stats
    
    async def search_domains(self, search_term: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search domains by name"""
        cursor = self.domains.find(
            {"domain": {"$regex": search_term, "$options": "i"}},
            {"_id": 0}
        ).sort("last_checked", -1).limit(limit)
        
        results = await cursor.to_list(length=limit)
        return results
    
    async def delete_domain(self, domain: str):
        """Delete a domain and its history"""
        domain_doc = await self.domains.find_one({"domain": domain})
        if domain_doc:
            domain_id = domain_doc['id']
            # Delete history
            await self.history.delete_many({"domain_id": domain_id})
            # Delete domain
            await self.domains.delete_one({"domain": domain})
    
    async def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recently detected domains"""
        cursor = self.domains.find(
            {},
            {"_id": 0}
        ).sort("first_seen", -1).limit(limit)
        
        results = await cursor.to_list(length=limit)
        return results
    
    async def get_recent_changes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently changed domains"""
        cursor = self.domains.find(
            {"content_changed": True},
            {"_id": 0}
        ).sort("last_checked", -1).limit(limit)
        
        results = await cursor.to_list(length=limit)
        return results
    
    async def get_domains_by_category(self) -> Dict[str, int]:
        """Get domain counts by category"""
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}}
        ]
        results = await self.domains.aggregate(pipeline).to_list(length=None)
        return {r['_id'] or 'uncategorized': r['count'] for r in results}
    
    async def get_timeline_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get domain discovery timeline for the last N days"""
        pipeline = [
            {
                "$project": {
                    "date": {"$substr": ["$first_seen", 0, 10]},
                    "domain": 1
                }
            },
            {
                "$group": {
                    "_id": "$date",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id": 1}
            },
            {
                "$limit": days
            }
        ]
        results = await self.domains.aggregate(pipeline).to_list(length=None)
        return [{"date": r['_id'], "count": r['count']} for r in results]


# === Convenience Functions ===

def get_db() -> DomainDB:
    """Get database instance"""
    return DomainDB()


# Initialize indexes on module import
async def init_db():
    """Initialize database and create indexes"""
    db_instance = get_db()
    await db_instance._ensure_indexes()
    print(f"✓ Database initialized: {DB_NAME}")
