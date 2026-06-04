from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ...database import get_mongo_db, execute_query
from ...main import require_role
from datetime import datetime
import secrets

router = APIRouter(dependencies=[Depends(require_role(["keeper"]))])
templates = Jinja2Templates(directory="app/templates")

@router.get("/logs", response_class=HTMLResponse)
async def get_logs_page(request: Request):
    user_id = request.session.get("user_id")
    keeper_row = execute_query("SELECT keeper_id FROM keepers WHERE user_id = %s", (user_id,))
    assigned_pokemon = []
    if keeper_row:
        assigned_pokemon = execute_query("""
            SELECT p.pokemon_id, p.nickname 
            FROM pokemon p JOIN pokemon_keepers pk ON p.pokemon_id = pk.pokemon_id 
            WHERE pk.keeper_id = %s
        """, (keeper_row[0]['keeper_id'],))
        
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
        
    return templates.TemplateResponse("keeper/logs.html", {
        "request": request,
        "assigned_pokemon": assigned_pokemon,
        "csrf_token": request.session["csrf_token"]
    })

@router.post("/logs")
async def create_log(
    request: Request,
    pokemon_id: int = Form(...),
    behavior: str = Form(...),
    mood: str = Form(...),
    trigger_reason: str = Form(None)
):
    db = await get_mongo_db()
    logs_collection = db["pokemon_behavior_logs"]
    
    log_document = {
        "pokemon_id": pokemon_id,
        "keeper_user_id": request.session.get("user_id"),
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "time": datetime.utcnow().strftime("%H:%M:%S"),
        "behavior": behavior,
        "mood": mood,
        "trigger": trigger_reason
    }
    
    await logs_collection.insert_one(log_document)
    
    return RedirectResponse(url="/keeper/dashboard?msg=log_added", status_code=303)


@router.get("/incidents", response_class=HTMLResponse)
async def get_incidents_page(request: Request):
    habitats = execute_query("SELECT habitat_id, habitat_name FROM habitats")
    
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
        
    return templates.TemplateResponse("keeper/incidents.html", {
        "request": request,
        "habitats": habitats,
        "csrf_token": request.session["csrf_token"]
    })

@router.post("/incidents")
async def create_incident(
    request: Request,
    pokemon_id: int = Form(None), # Optional, might just be a habitat issue
    habitat_id: int = Form(...),
    severity: str = Form(...),
    description: str = Form(...),
    actions_taken: str = Form(...) # Comma separated for simplicity
):
    db = await get_mongo_db()
    incidents_collection = db["incident_reports"]
    
    actions_list = [action.strip() for action in actions_taken.split(",") if action.strip()]
    
    incident_document = {
        "incident_id": f"INC-{secrets.token_hex(4).upper()}",
        "keeper_user_id": request.session.get("user_id"),
        "date_reported": datetime.utcnow().isoformat(),
        "pokemon_id": pokemon_id,
        "habitat_id": habitat_id,
        "severity": severity,
        "description": description,
        "actions_taken": actions_list
    }
    
    await incidents_collection.insert_one(incident_document)
    return RedirectResponse(url="/keeper/dashboard?msg=incident_reported", status_code=303)
