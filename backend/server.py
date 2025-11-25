from fastapi import FastAPI, APIRouter, HTTPException, Body, Query, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import json
import csv
import io
import subprocess
import asyncio
import threading

# Import db_manager
from .db_manager import get_db, init_db

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(Path(__file__).parent / '.env')

# Create the main app without a prefix
app = FastAPI(title="NRD Monitoring Dashboard API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class DomainResponse(BaseModel):
    id: str
    domain: str
    first_seen: str
    last_checked: str
    is_active: bool
    content_hash: str
    content_changed: bool
    has_profile: bool
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    category: Optional[str] = None
    risk_level: Optional[str] = 'unknown'
    created_at: str
    updated_at: str

class DomainHistoryResponse(BaseModel):
    id: str
    domain_id: str
    checked_at: str
    is_active: bool
    content_hash: Optional[str] = None
    content_changed: bool
    screenshot_taken: bool

class StatsResponse(BaseModel):
    total: int
    active: int
    inactive: int
    changed: int
    with_profiles: int
    golden_matches: int
    category_golden: int
    category_absa: int
    category_coza: int
    category_africa: int
    category_pattern: int

class DomainUpdateRequest(BaseModel):
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    has_profile: Optional[bool] = None
    risk_level: Optional[str] = None

class PatternResponse(BaseModel):
    name: str
    patterns: List[str]
    enabled: bool

class WhitelistDomain(BaseModel):
    domain: str

class WorkflowStatus(BaseModel):
    running: bool
    current_step: Optional[str] = None
    message: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    progress: Optional[int] = None


# ============================================================================
# DOMAIN ENDPOINTS
# ============================================================================

def load_ignored_domains():
    """Load the list of ignored domains from IgnoreDomains.txt"""
    ignored_domains = set()
    ignore_file = ROOT_DIR / "Whitelist" / "IgnoreDomains.txt"
    
    if ignore_file.exists():
        with open(ignore_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Normalize domain (remove http://, www., trailing slashes)
                    domain = line.lower()
                    if "://" in domain:
                        domain = domain.split("://", 1)[1]
                    if "/" in domain:
                        domain = domain.split("/", 1)[0]
                    if domain.startswith("www."):
                        domain = domain[4:]
                    domain = domain.rstrip('.')
                    ignored_domains.add(domain)
    
    return ignored_domains

@api_router.get("/")
async def root():
    return {"message": "NRD Monitoring API v1.0"}

@api_router.get("/domains/{domain}/profile")
async def get_domain_profile(domain: str):
    """Get the enriched profile for a domain if it exists."""
    profile_dir = ROOT_DIR / "Output" / "Domain_Profiles"
    profile_filename = f"{domain.replace('.', '_')}_profile.json"
    profile_path = profile_dir / profile_filename
    
    if not profile_path.exists():
        raise HTTPException(status_code=404, detail=f"No profile found for {domain}")
    
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        return profile_data
    except Exception as e:
        logging.error(f"Error reading profile for {domain}: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading profile: {str(e)}")

@api_router.post("/domains/{domain}/profile/generate")
async def generate_domain_profile(domain: str, background_tasks: BackgroundTasks):
    """Trigger generation of an enriched profile for a domain."""
    # Check if domain_profiler.py exists
    profiler_script = ROOT_DIR / "domain_profiler.py"
    if not profiler_script.exists():
        raise HTTPException(status_code=404, detail="Domain profiler script not found")
    
    # Find Python interpreter
    python_cmd = None
    venv_python = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        python_cmd = str(venv_python)
    else:
        python_cmd = "python"
    
    async def run_profiler():
        """Run domain profiler in background and update database."""
        try:
            # Run the domain_profiler.py script directly with the domain as argument
            result = subprocess.run(
                [python_cmd, str(profiler_script), domain],
                cwd=str(ROOT_DIR),
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode != 0:
                logging.error(f"Domain profiler failed for {domain}: {result.stderr}")
            else:
                logging.info(f"Successfully generated profile for {domain}")
                # Update database to mark domain as having a profile
                db = get_db()
                await db.update_profile_status(domain, True)
                
        except Exception as e:
            logging.error(f"Error generating profile for {domain}: {e}")
    
    # Run in background
    background_tasks.add_task(run_profiler)
    
    return {
        "message": f"Profile generation started for {domain}",
        "status": "processing"
    }

@api_router.post("/domains/profiles/sync")
async def sync_domain_profiles():
    """Sync has_profile flags in database based on existing profile files."""
    profile_dir = ROOT_DIR / "Output" / "Domain_Profiles"
    
    if not profile_dir.exists():
        return {"message": "Profile directory does not exist", "synced": 0}
    
    db = get_db()
    synced_count = 0
    
    # Get all profile files
    profile_files = list(profile_dir.glob("*_profile.json"))
    
    for profile_file in profile_files:
        # Extract domain name from filename (e.g., "absa-fraud_co_za_profile.json" -> "absa-fraud.co.za")
        filename = profile_file.stem  # Remove .json extension
        domain_with_underscores = filename.replace("_profile", "")  # Remove _profile suffix
        # Convert underscores back to dots (reverse of domain.replace('.', '_'))
        domain = domain_with_underscores.replace("_", ".")
        
        try:
            await db.update_profile_status(domain, True)
            synced_count += 1
            logging.info(f"Synced profile status for {domain}")
        except Exception as e:
            logging.error(f"Failed to sync profile status for {domain}: {e}")
    
    return {
        "message": f"Synced {synced_count} domain profiles",
        "synced": synced_count,
        "total_files": len(profile_files)
    }

@api_router.get("/domains", response_model=Dict[str, Any])
async def get_domains(
    active_only: bool = Query(False),
    changed_only: bool = Query(False),
    with_profile_only: bool = Query(False),
    category: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),  # Comma-separated tags
    search: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
    sort_by: str = Query("last_checked"),
    sort_order: int = Query(-1)
):
    """Get all domains with filters and pagination"""
    db = get_db()
    
    # Parse tags if provided
    tags_list = tags.split(',') if tags else None
    
    # Load ignored domains
    ignored_domains = load_ignored_domains()
    
    domains = await db.get_all_domains(
        active_only=active_only,
        changed_only=changed_only,
        with_profile_only=with_profile_only,
        category=category,
        tags=tags_list,
        search_term=search,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Filter out ignored domains
    filtered_domains = [
        d for d in domains 
        if d['domain'].lower() not in ignored_domains
    ]
    
    total = await db.get_domain_count(
        active_only=active_only,
        changed_only=changed_only,
        with_profile_only=with_profile_only,
        category=category,
        tags=tags_list,
        search_term=search
    )
    
    # Adjust total count by subtracting ignored domains
    # (This is an approximation - for exact count we'd need to query differently)
    total_ignored = len([d for d in domains if d['domain'].lower() in ignored_domains])
    adjusted_total = max(0, total - total_ignored)
    
    return {
        "domains": filtered_domains,
        "total": adjusted_total,
        "limit": limit,
        "offset": offset
    }

@api_router.get("/domains/{domain}")
async def get_domain(domain: str):
    """Get a single domain by name"""
    db = get_db()
    result = await db.get_domain(domain)
    
    if not result:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    return result

@api_router.put("/domains/{domain}")
async def update_domain(domain: str, update: DomainUpdateRequest):
    """Update domain information"""
    db = get_db()
    
    # Check if domain exists
    existing = await db.get_domain(domain)
    if not existing:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    # Build update dictionary
    update_data = {}
    
    if update.notes is not None:
        update_data['notes'] = update.notes
    
    if update.tags is not None:
        update_data['tags'] = update.tags
    
    if update.has_profile is not None:
        update_data['has_profile'] = update.has_profile
    
    if update.risk_level is not None:
        update_data['risk_level'] = update.risk_level
    
    # Update domain with all fields at once
    if update_data:
        await db.domains.update_one(
            {"domain": domain},
            {"$set": update_data}
        )
    
    # Return updated domain
    result = await db.get_domain(domain)
    return result

@api_router.delete("/domains/{domain}")
async def delete_domain(domain: str):
    """Delete a domain"""
    db = get_db()
    
    existing = await db.get_domain(domain)
    if not existing:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    await db.delete_domain(domain)
    return {"message": "Domain deleted successfully"}

@api_router.get("/domains/{domain}/history")
async def get_domain_history(domain: str, limit: int = Query(50)):
    """Get history for a domain"""
    db = get_db()
    
    history = await db.get_domain_history(domain, limit=limit)
    return {"domain": domain, "history": history}


# New add to Ignore endpoint

@api_router.post("/domains/{domain}/ignore")
async def add_to_ignore_list(domain: str):
    """Add a domain to the ignore list"""
    try:
        ignore_file = ROOT_DIR / "Whitelist" / "IgnoreDomains.txt"
        
        # Read existing domains
        existing_domains = set()
        if ignore_file.exists():
            with open(ignore_file, 'r', encoding='utf-8') as f:
                existing_domains = {line.strip() for line in f if line.strip() and not line.startswith('#')}
        
        # Check if already exists
        if domain in existing_domains:
            return {"success": False, "message": "Domain already in ignore list"}
        
        # Append the domain
        with open(ignore_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{domain}")
        
        logger.info(f"Added {domain} to ignore list")
        return {"success": True, "message": f"Added {domain} to ignore list"}
    except Exception as e:
        logger.error(f"Failed to add domain to ignore list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STATISTICS & ANALYTICS ENDPOINTS
# ============================================================================

@api_router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get dashboard statistics"""
    db = get_db()
    stats = await db.get_stats()
    return stats

@api_router.get("/analytics/recent-activity")
async def get_recent_activity(limit: int = Query(20)):
    """Get recently detected domains"""
    db = get_db()
    domains = await db.get_recent_activity(limit=limit)
    return {"recent_activity": domains}

@api_router.get("/analytics/recent-changes")
async def get_recent_changes(limit: int = Query(10)):
    """Get recently changed domains"""
    db = get_db()
    domains = await db.get_recent_changes(limit=limit)
    return {"recent_changes": domains}

@api_router.get("/analytics/by-category")
async def get_by_category():
    """Get domain counts by category"""
    db = get_db()
    categories = await db.get_domains_by_category()
    return {"categories": categories}

@api_router.get("/analytics/timeline")
async def get_timeline(days: int = Query(30)):
    """Get domain discovery timeline"""
    db = get_db()
    timeline = await db.get_timeline_data(days=days)
    return {"timeline": timeline}


# ============================================================================
# PATTERN MANAGEMENT ENDPOINTS
# ============================================================================

@api_router.get("/patterns")
async def get_patterns():
    """Get all pattern files"""
    patterns_dir = ROOT_DIR / "Patterns"
    
    if not patterns_dir.exists():
        return {"patterns": []}
    
    pattern_files = ["typos.txt", "presuf.txt", "TLD.txt", "keywords.txt"]
    patterns = []
    
    for filename in pattern_files:
        file_path = patterns_dir / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            patterns.append({
                "name": filename.replace('.txt', ''),
                "patterns": content,
                "enabled": True,
                "count": len(content)
            })
    
    return {"patterns": patterns}

@api_router.put("/patterns/{pattern_name}")
async def update_pattern(pattern_name: str, patterns: List[str] = Body(...)):
    """Update a pattern file"""
    patterns_dir = ROOT_DIR / "Patterns"
    patterns_dir.mkdir(exist_ok=True)
    
    file_path = patterns_dir / f"{pattern_name}.txt"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(patterns))
    
    return {"message": f"Pattern {pattern_name} updated successfully", "count": len(patterns)}


# ============================================================================
# WHITELIST MANAGEMENT ENDPOINTS
# ============================================================================

@api_router.get("/whitelist/ignore")
async def get_ignore_domains():
    """Get ignore domains (safe list)"""
    whitelist_dir = ROOT_DIR / "Whitelist"
    ignore_file = whitelist_dir / "IgnoreDomains.txt"
    
    if not ignore_file.exists():
        return {"domains": []}
    
    with open(ignore_file, 'r', encoding='utf-8') as f:
        domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    return {"domains": domains}

@api_router.post("/whitelist/ignore")
async def add_ignore_domain(domain: WhitelistDomain):
    """Add domain to ignore list"""
    whitelist_dir = ROOT_DIR / "Whitelist"
    whitelist_dir.mkdir(exist_ok=True)
    ignore_file = whitelist_dir / "IgnoreDomains.txt"
    
    # Read existing domains
    existing = []
    if ignore_file.exists():
        with open(ignore_file, 'r', encoding='utf-8') as f:
            existing = [line.strip() for line in f if line.strip()]
    
    # Add new domain if not exists
    if domain.domain not in existing:
        existing.append(domain.domain)
        
        with open(ignore_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(existing))
    
    return {"message": "Domain added to ignore list", "domain": domain.domain}

@api_router.delete("/whitelist/ignore/{domain}")
async def remove_ignore_domain(domain: str):
    """Remove domain from ignore list"""
    whitelist_dir = ROOT_DIR / "Whitelist"
    ignore_file = whitelist_dir / "IgnoreDomains.txt"
    
    if not ignore_file.exists():
        raise HTTPException(status_code=404, detail="Ignore list not found")
    
    # Read existing domains
    with open(ignore_file, 'r', encoding='utf-8') as f:
        existing = [line.strip() for line in f if line.strip()]
    
    # Remove domain
    if domain in existing:
        existing.remove(domain)
        
        with open(ignore_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(existing))
        
        return {"message": "Domain removed from ignore list"}
    else:
        raise HTTPException(status_code=404, detail="Domain not found in ignore list")

@api_router.get("/whitelist/included")
async def get_included_domains():
    """Get included domains (confirmed threats)"""
    whitelist_dir = ROOT_DIR / "Whitelist"
    include_file = whitelist_dir / "IncludedHits.txt"
    
    if not include_file.exists():
        return {"domains": []}
    
    with open(include_file, 'r', encoding='utf-8') as f:
        domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    return {"domains": domains}


# ============================================================================
# WORKFLOW MANAGEMENT ENDPOINTS
# ============================================================================

# Global workflow status tracker
workflow_status = {
    "running": False,
    "current_step": None,
    "message": "No workflow has been run yet",
    "start_time": None,
    "end_time": None,
    "progress": 0,
    "logs": []  # Store actual stdout/stderr output
}

def run_workflow_sync():
    """Run workflow synchronously in background thread"""
    global workflow_status
    
    try:
        main_py = ROOT_DIR / "main.py"
        
        if not main_py.exists():
            workflow_status["message"] = "main.py not found"
            workflow_status["running"] = False
            return
        
        # Find python executable (prefer venv)
        venv_python = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
        python_cmd = str(venv_python) if venv_python.exists() else "python"
        
        logger.info(f"Starting workflow with: {python_cmd} {main_py}")
        
        # Run with unbuffered output (-u flag)
        process = subprocess.Popen(
            [python_cmd, "-u", str(main_py)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=str(ROOT_DIR),
            text=True,
            bufsize=0  # Unbuffered
        )
        
        # Read output line by line in real-time
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line_text = line.rstrip()
                workflow_status["logs"].append(line_text)
                if len(workflow_status["logs"]) > 1000:
                    workflow_status["logs"] = workflow_status["logs"][-1000:]
                logger.info(f"Workflow: {line_text}")
        
        process.wait()
        
        if process.returncode == 0:
            workflow_status["message"] = "✅ Workflow completed successfully!"
            workflow_status["current_step"] = "completed"
            workflow_status["progress"] = 100
        else:
            workflow_status["message"] = f"❌ Workflow failed with exit code {process.returncode}"
            workflow_status["current_step"] = "failed"
            logger.error(f"Workflow failed with exit code {process.returncode}")
    
    except Exception as e:
        workflow_status["message"] = f"❌ Error: {str(e)}"
        workflow_status["current_step"] = "error"
        workflow_status["progress"] = 0
        logger.error(f"Workflow error: {str(e)}", exc_info=True)
    
    finally:
        workflow_status["running"] = False
        workflow_status["end_time"] = datetime.now(timezone.utc).isoformat()

async def run_main_workflow():
    """Run the main.py workflow in background"""
    global workflow_status
    
    workflow_status["running"] = True
    workflow_status["current_step"] = "starting"
    workflow_status["message"] = "Initializing workflow..."
    workflow_status["start_time"] = datetime.now(timezone.utc).isoformat()
    workflow_status["logs"] = []  # Clear previous logs
    
    # Run in thread to avoid blocking
    thread = threading.Thread(target=run_workflow_sync, daemon=True)
    thread.start()

@api_router.post("/workflow/run")
async def trigger_workflow(background_tasks: BackgroundTasks):
    """Trigger the main workflow"""
    global workflow_status
    
    if workflow_status["running"]:
        raise HTTPException(status_code=400, detail="Workflow is already running")
    
    background_tasks.add_task(run_main_workflow)
    
    return {"message": "Workflow started", "status": "running"}

@api_router.get("/workflow/status")
async def get_workflow_status():
    """Get current workflow status"""
    return workflow_status


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================

@api_router.get("/export/csv")
async def export_csv(
    active_only: bool = Query(False),
    changed_only: bool = Query(False)
):
    """Export domains to CSV"""
    db = get_db()
    
    domains = await db.get_all_domains(
        active_only=active_only,
        changed_only=changed_only
    )
    
    # Create CSV in memory
    output = io.StringIO()
    if domains:
        fieldnames = domains[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(domains)
    
    # Return as streaming response
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=domains_export.csv"}
    )

@api_router.get("/export/json")
async def export_json(
    active_only: bool = Query(False),
    changed_only: bool = Query(False)
):
    """Export domains to JSON"""
    db = get_db()
    
    domains = await db.get_all_domains(
        active_only=active_only,
        changed_only=changed_only
    )
    
    return StreamingResponse(
        iter([json.dumps({"domains": domains}, indent=2)]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=domains_export.json"}
    )


# ============================================================================
# SCREENSHOT ENDPOINTS
# ============================================================================

@api_router.get("/screenshots/{domain}")
async def get_screenshots(domain: str):
    """Get screenshots for a domain"""
    screenshots_dir = ROOT_DIR / "Output" / "Screenshots"
    domain_dir = screenshots_dir / domain.replace('.', '_')
    
    if not domain_dir.exists():
        return {"screenshots": []}
    
    screenshots = []
    for file in sorted(domain_dir.glob("*.png"), reverse=True):
        screenshots.append({
            "filename": file.name,
            "timestamp": file.stem,
            "path": str(file.relative_to(ROOT_DIR)),
            "size": file.stat().st_size
        })
    
    return {"domain": domain, "screenshots": screenshots}

@api_router.get("/screenshots/{domain}/{filename}")
async def get_screenshot_file(domain: str, filename: str):
    """Get a screenshot file"""
    screenshots_dir = ROOT_DIR / "Output" / "Screenshots"
    domain_dir = screenshots_dir / domain.replace('.', '_')
    file_path = domain_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    return FileResponse(file_path, media_type="image/png")

@api_router.post("/screenshots/{domain}/capture")
async def capture_screenshot(domain: str, background_tasks: BackgroundTasks):
    """Capture a screenshot for a domain"""
    screenshots_dir = ROOT_DIR / "Output" / "Screenshots"
    domain_dir = screenshots_dir / domain.replace('.', '_')
    domain_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if playwright is available
    try:
        from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    except ImportError:
        raise HTTPException(status_code=503, detail="Screenshot service unavailable (Playwright not installed)")
    
    async def take_screenshot():
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': 1440, 'height': 900},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = await context.new_page()
                
                # Try both https and http
                success = False
                for protocol in ['https', 'http']:
                    try:
                        url = f"{protocol}://{domain}"
                        await page.goto(url, wait_until='networkidle', timeout=15000)
                        
                        # Save screenshot
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_path = domain_dir / f"{timestamp}.png"
                        await page.screenshot(path=str(screenshot_path), full_page=False)
                        
                        success = True
                        logger.info(f"Screenshot captured for {domain}")
                        break
                    except Exception as e:
                        logger.debug(f"Failed to capture {protocol}://{domain}: {str(e)}")
                        continue
                
                await browser.close()
                
                if not success:
                    logger.warning(f"Failed to capture screenshot for {domain}")
                    
        except Exception as e:
            logger.error(f"Error capturing screenshot for {domain}: {str(e)}")
    
    # Add to background tasks
    background_tasks.add_task(take_screenshot)
    
    return {"message": f"Screenshot capture initiated for {domain}", "status": "processing"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()
    logger.info("NRD Monitoring Dashboard API started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("NRD Monitoring Dashboard API shutdown")