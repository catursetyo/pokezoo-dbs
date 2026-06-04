from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ...database import execute_query
from ...main import require_role

router = APIRouter(dependencies=[Depends(require_role(["admin"]))])
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    stats = {
        "pokemon_count": execute_query("SELECT COUNT(*) as count FROM pokemon")[0]['count'],
        "habitats_count": execute_query("SELECT COUNT(*) as count FROM habitats")[0]['count'],
        "keepers_count": execute_query("SELECT COUNT(*) as count FROM keepers")[0]['count'],
        "tickets_sold": execute_query("SELECT COUNT(*) as count FROM tickets")[0]['count']
    }
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "stats": stats,
        "role": request.session.get("role")
    })
