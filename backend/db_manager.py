import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
import aiosqlite
import json
from dotenv import load_dotenv
import uuid

# === Path Setup ===
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / "backend" / '.env')

# SQLite database path
DB_PATH = ROOT_DIR / "nrd_monitoring.db"


class DomainDB:
    """Database manager for domain tracking - SQLite version"""
    
    def __init__(self, db_path: Path = DB_PATH):
        """Initialize database connection"""
        self.db_path = db_path
    
    def get_connection(self):
        """Get database connection - returns a connection context"""
        return aiosqlite.connect(str(self.db_path))
    
    async def _ensure_tables(self):
        """Create tables if they don't exist"""
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            # Create domains table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS domains (
                    id TEXT PRIMARY KEY,
                    domain TEXT UNIQUE NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_checked TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 0,
                    content_hash TEXT DEFAULT '',
                    content_changed INTEGER NOT NULL DEFAULT 0,
                    has_profile INTEGER NOT NULL DEFAULT 0,
                    tags TEXT DEFAULT '[]',
                    notes TEXT DEFAULT '',
                    category TEXT,
                    risk_level TEXT DEFAULT 'unknown',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Create domain_history table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS domain_history (
                    id TEXT PRIMARY KEY,
                    domain_id TEXT NOT NULL,
                    checked_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 0,
                    content_hash TEXT,
                    content_changed INTEGER NOT NULL DEFAULT 0,
                    screenshot_taken INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (domain_id) REFERENCES domains(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_domain ON domains(domain)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_is_active ON domains(is_active)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_first_seen ON domains(first_seen)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_last_checked ON domains(last_checked)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_content_changed ON domains(content_changed)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_category ON domains(category)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_risk_level ON domains(risk_level)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_history_domain_id ON domain_history(domain_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_history_checked_at ON domain_history(checked_at)")
            
            await db.commit()
    
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
        
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            # Check if domain exists
            cursor = await db.execute("SELECT id, risk_level FROM domains WHERE domain = ?", (domain,))
            existing = await cursor.fetchone()
            
            if existing:
                # Update existing domain
                domain_id = existing['id']
                # Only update risk_level if it's explicitly provided or doesn't exist
                if risk_level or not existing['risk_level']:
                    update_risk_level = risk_level
                else:
                    update_risk_level = existing['risk_level']
                
                await db.execute("""
                    UPDATE domains SET
                        last_checked = ?,
                        is_active = ?,
                        content_hash = ?,
                        content_changed = ?,
                        has_profile = ?,
                        tags = ?,
                        notes = ?,
                        category = ?,
                        risk_level = ?,
                        updated_at = ?
                    WHERE domain = ?
                """, (
                    last_checked,
                    int(is_active),
                    content_hash or "",
                    int(content_changed),
                    int(has_profile),
                    json.dumps(tags),
                    notes,
                    category,
                    update_risk_level,
                    now,
                    domain
                ))
            else:
                # Insert new domain with risk_level
                domain_id = str(uuid.uuid4())
                await db.execute("""
                    INSERT INTO domains (
                        id, domain, first_seen, last_checked, is_active, content_hash,
                        content_changed, has_profile, tags, notes, category, risk_level,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    domain_id, domain, first_seen, last_checked, int(is_active),
                    content_hash or "", int(content_changed), int(has_profile),
                    json.dumps(tags), notes, category, risk_level, now, now
                ))
            
            await db.commit()
        
        return domain_id
    
    async def add_history_entry(self, domain_id: str, checked_at: Optional[str] = None,
                         is_active: bool = False, content_hash: Optional[str] = None,
                         content_changed: bool = False, screenshot_taken: bool = False):
        """Add a history entry for a domain scan"""
        checked_at = checked_at or datetime.now(timezone.utc).isoformat()
        
        history_id = str(uuid.uuid4())
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            await db.execute("""
                INSERT INTO domain_history (
                    id, domain_id, checked_at, is_active, content_hash,
                    content_changed, screenshot_taken
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                history_id, domain_id, checked_at, int(is_active),
                content_hash, int(content_changed), int(screenshot_taken)
            ))
            await db.commit()
    
    async def get_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get a single domain by name"""
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM domains WHERE domain = ?", (domain,))
            row = await cursor.fetchone()
            
            if row:
                result = dict(row)
                result['is_active'] = bool(result['is_active'])
                result['content_changed'] = bool(result['content_changed'])
                result['has_profile'] = bool(result['has_profile'])
                result['tags'] = json.loads(result['tags']) if result['tags'] else []
                return result
            return None
    
    async def get_domain_by_id(self, domain_id: str) -> Optional[Dict[str, Any]]:
        """Get a single domain by ID"""
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM domains WHERE id = ?", (domain_id,))
            row = await cursor.fetchone()
            
            if row:
                result = dict(row)
                result['is_active'] = bool(result['is_active'])
                result['content_changed'] = bool(result['content_changed'])
                result['has_profile'] = bool(result['has_profile'])
                result['tags'] = json.loads(result['tags']) if result['tags'] else []
                return result
            return None
    
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
        conditions = []
        params = []
        
        if active_only:
            conditions.append("is_active = 1")
        
        if changed_only:
            conditions.append("content_changed = 1")
        
        if with_profile_only:
            conditions.append("has_profile = 1")
        
        if category:
            conditions.append("category = ?")
            params.append(category)
        
        if search_term:
            conditions.append("domain LIKE ?")
            params.append(f"%{search_term}%")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        order_dir = "DESC" if sort_order == -1 else "ASC"
        
        query = f"SELECT * FROM domains WHERE {where_clause} ORDER BY {sort_by} {order_dir}"
        
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        elif offset:
            query += f" OFFSET {offset}"
        
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            results = []
            for row in rows:
                result = dict(row)
                result['is_active'] = bool(result['is_active'])
                result['content_changed'] = bool(result['content_changed'])
                result['has_profile'] = bool(result['has_profile'])
                result['tags'] = json.loads(result['tags']) if result['tags'] else []
                
                # Filter by tags if specified
                if tags:
                    if any(tag in result['tags'] for tag in tags):
                        results.append(result)
                else:
                    results.append(result)
            
            return results
    
    async def get_domain_count(self, active_only: bool = False, 
                       changed_only: bool = False,
                       with_profile_only: bool = False,
                       category: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       search_term: Optional[str] = None) -> int:
        """Get count of domains with filters"""
        conditions = []
        params = []
        
        if active_only:
            conditions.append("is_active = 1")
        
        if changed_only:
            conditions.append("content_changed = 1")
        
        if with_profile_only:
            conditions.append("has_profile = 1")
        
        if category:
            conditions.append("category = ?")
            params.append(category)
        
        if search_term:
            conditions.append("domain LIKE ?")
            params.append(f"%{search_term}%")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # For tags, we need to filter in Python since JSON querying is complex
        if tags:
            # Get all matching domains and filter by tags
            all_domains = await self.get_all_domains(
                active_only=active_only,
                changed_only=changed_only,
                with_profile_only=with_profile_only,
                category=category,
                tags=tags,
                search_term=search_term
            )
            return len(all_domains)
        
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(f"SELECT COUNT(*) as count FROM domains WHERE {where_clause}", params)
            row = await cursor.fetchone()
            return row['count'] if row else 0
    
    async def get_domain_history(self, domain: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get history entries for a domain"""
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            # Get domain_id
            cursor = await db.execute("SELECT id FROM domains WHERE domain = ?", (domain,))
            domain_row = await cursor.fetchone()
            
            if not domain_row:
                return []
            
            domain_id = domain_row['id']
            
            # Get history
            cursor = await db.execute("""
                SELECT * FROM domain_history 
                WHERE domain_id = ? 
                ORDER BY checked_at DESC 
                LIMIT ?
            """, (domain_id, limit))
            
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                result = dict(row)
                result['is_active'] = bool(result['is_active'])
                result['content_changed'] = bool(result['content_changed'])
                result['screenshot_taken'] = bool(result['screenshot_taken'])
                results.append(result)
            
            return results
    
    async def update_profile_status(self, domain: str, has_profile: bool):
        """Update profile existence status for a domain"""
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            await db.execute("""
                UPDATE domains SET 
                    has_profile = ?,
                    updated_at = ?
                WHERE domain = ?
            """, (int(has_profile), datetime.now(timezone.utc).isoformat(), domain))
            await db.commit()
    
    async def update_domain_notes(self, domain: str, notes: str):
        """Update notes for a domain"""
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            await db.execute("""
                UPDATE domains SET 
                    notes = ?,
                    updated_at = ?
                WHERE domain = ?
            """, (notes, datetime.now(timezone.utc).isoformat(), domain))
            await db.commit()
    
    async def update_risk_level(self, domain: str, tags: List[str]):
        """Update tags for a domain"""
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            await db.execute("""
                UPDATE domains SET 
                    tags = ?,
                    updated_at = ?
                WHERE domain = ?
            """, (json.dumps(tags), datetime.now(timezone.utc).isoformat(), domain))
            await db.commit()
    
    async def get_stats(self) -> Dict[str, int]:
        """Get statistics about domains"""
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            stats = {}
            
            # Total domains
            cursor = await db.execute("SELECT COUNT(*) as count FROM domains")
            stats['total'] = (await cursor.fetchone())['count']
            
            # Active domains
            cursor = await db.execute("SELECT COUNT(*) as count FROM domains WHERE is_active = 1")
            stats['active'] = (await cursor.fetchone())['count']
            
            # Inactive domains
            cursor = await db.execute("SELECT COUNT(*) as count FROM domains WHERE is_active = 0")
            stats['inactive'] = (await cursor.fetchone())['count']
            
            # Changed domains
            cursor = await db.execute("SELECT COUNT(*) as count FROM domains WHERE content_changed = 1")
            stats['changed'] = (await cursor.fetchone())['count']
            
            # Domains with profiles
            cursor = await db.execute("SELECT COUNT(*) as count FROM domains WHERE has_profile = 1")
            stats['with_profiles'] = (await cursor.fetchone())['count']
            
            # Golden matches
            cursor = await db.execute("SELECT COUNT(*) as count FROM domains WHERE category = 'golden'")
            stats['golden_matches'] = (await cursor.fetchone())['count']
            
            # By category
            cursor = await db.execute("SELECT COUNT(*) as count FROM domains WHERE category = 'golden'")
            stats['category_golden'] = (await cursor.fetchone())['count']
            
            cursor = await db.execute("SELECT COUNT(*) as count FROM domains WHERE category = 'absa'")
            stats['category_absa'] = (await cursor.fetchone())['count']
            
            cursor = await db.execute("SELECT COUNT(*) as count FROM domains WHERE category = 'coza'")
            stats['category_coza'] = (await cursor.fetchone())['count']
            
            cursor = await db.execute("SELECT COUNT(*) as count FROM domains WHERE category = 'africa'")
            stats['category_africa'] = (await cursor.fetchone())['count']
            
            cursor = await db.execute("SELECT COUNT(*) as count FROM domains WHERE category = 'pattern'")
            stats['category_pattern'] = (await cursor.fetchone())['count']
            
            return stats
    
    async def search_domains(self, search_term: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search domains by name"""
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM domains 
                WHERE domain LIKE ? 
                ORDER BY last_checked DESC 
                LIMIT ?
            """, (f"%{search_term}%", limit))
            
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                result = dict(row)
                result['is_active'] = bool(result['is_active'])
                result['content_changed'] = bool(result['content_changed'])
                result['has_profile'] = bool(result['has_profile'])
                result['tags'] = json.loads(result['tags']) if result['tags'] else []
                results.append(result)
            
            return results
    
    async def delete_domain(self, domain: str):
        """Delete a domain and its history"""
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            # Get domain_id
            cursor = await db.execute("SELECT id FROM domains WHERE domain = ?", (domain,))
            domain_row = await cursor.fetchone()
            
            if domain_row:
                domain_id = domain_row['id']
                # Delete history (CASCADE should handle this, but being explicit)
                await db.execute("DELETE FROM domain_history WHERE domain_id = ?", (domain_id,))
                # Delete domain
                await db.execute("DELETE FROM domains WHERE domain = ?", (domain,))
                await db.commit()
    
    async def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recently detected domains"""
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM domains 
                ORDER BY first_seen DESC 
                LIMIT ?
            """, (limit,))
            
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                result = dict(row)
                result['is_active'] = bool(result['is_active'])
                result['content_changed'] = bool(result['content_changed'])
                result['has_profile'] = bool(result['has_profile'])
                result['tags'] = json.loads(result['tags']) if result['tags'] else []
                results.append(result)
            
            return results
    
    async def get_recent_changes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently changed domains"""
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM domains 
                WHERE content_changed = 1
                ORDER BY last_checked DESC 
                LIMIT ?
            """, (limit,))
            
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                result = dict(row)
                result['is_active'] = bool(result['is_active'])
                result['content_changed'] = bool(result['content_changed'])
                result['has_profile'] = bool(result['has_profile'])
                result['tags'] = json.loads(result['tags']) if result['tags'] else []
                results.append(result)
            
            return results
    
    async def get_domains_by_category(self) -> Dict[str, int]:
        """Get domain counts by category"""
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT category, COUNT(*) as count 
                FROM domains 
                GROUP BY category
            """)
            
            rows = await cursor.fetchall()
            return {row['category'] or 'uncategorized': row['count'] for row in rows}
    
    async def get_timeline_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get domain discovery timeline for the last N days"""
        async with self.get_connection() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT 
                    substr(first_seen, 1, 10) as date,
                    COUNT(*) as count
                FROM domains
                GROUP BY date
                ORDER BY date ASC
                LIMIT ?
            """, (days,))
            
            rows = await cursor.fetchall()
            return [{"date": row['date'], "count": row['count']} for row in rows]


# === Convenience Functions ===

_db_instance = None

def get_db() -> DomainDB:
    """Get database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DomainDB()
    return _db_instance


# Initialize database on module import
async def init_db():
    """Initialize database and create tables"""
    db_instance = get_db()
    await db_instance._ensure_tables()
    print(f"✓ Database initialized: {DB_PATH}")

