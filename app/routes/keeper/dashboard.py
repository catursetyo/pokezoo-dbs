from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ...database import execute_query
from ...main import require_role
import secrets

router = APIRouter(dependencies=[Depends(require_role(["keeper"]))])
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user_id = request.session.get("user_id")
    
    # Get keeper_id
    keeper_row = execute_query("SELECT keeper_id, name, shift FROM keepers WHERE user_id = %s", (user_id,))
    if not keeper_row:
        return HTMLResponse("Keeper profile not found. Please contact admin.", status_code=404)
        
    keeper = keeper_row[0]
    keeper_id = keeper['keeper_id']
    
    # Get assigned pokemon
    assigned_pokemon = execute_query("""
        SELECT p.pokemon_id, p.nickname, s.species_name, p.health_status, pk.assigned_since
        FROM pokemon p
        JOIN pokemon_species s ON p.species_id = s.species_id
        JOIN pokemon_keepers pk ON p.pokemon_id = pk.pokemon_id
        WHERE pk.keeper_id = %s
    """, (keeper_id,))
    
    # Get feeding schedules for today or pending
    schedules = execute_query("""
        SELECT fs.feeding_id, p.nickname, f.food_name, fs.feeding_time, fs.status
        FROM feeding_schedules fs
        JOIN pokemon p ON fs.pokemon_id = p.pokemon_id
        JOIN foods f ON fs.food_id = f.food_id
        WHERE fs.keeper_id = %s AND fs.status = 'scheduled'
        ORDER BY fs.feeding_time ASC
    """, (keeper_id,))
    
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
        
    return templates.TemplateResponse("keeper/dashboard.html", {
        "request": request,
        "keeper": keeper,
        "assigned_pokemon": assigned_pokemon,
        "schedules": schedules,
        "csrf_token": request.session["csrf_token"]
    })

@router.post("/feedings/update/{feeding_id}")
async def update_feeding(request: Request, feeding_id: int, status: str = Form(...)):
    user_id = request.session.get("user_id")
    
    # Basic authorization check to ensure the feeding belongs to this keeper
    keeper_row = execute_query("SELECT keeper_id FROM keepers WHERE user_id = %s", (user_id,))
    if keeper_row:
        keeper_id = keeper_row[0]['keeper_id']
        execute_query("""
            UPDATE feeding_schedules 
            SET status = %s 
            WHERE feeding_id = %s AND keeper_id = %s
        """, (status, feeding_id, keeper_id))
    
    return RedirectResponse(url="/keeper/dashboard", status_code=303)
