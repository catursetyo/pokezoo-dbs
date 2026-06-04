from ...main import require_role
from fastapi import APIRouter, Request, Form, Depends
from typing import List
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ...database import execute_query
import secrets

router = APIRouter(dependencies=[Depends(require_role(["admin"]))])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_species(request: Request):
    query = """
        SELECT 
            ps.species_id, 
            ps.species_name, 
            ps.rarity,
            GROUP_CONCAT(pt.type_name ORDER BY pt.type_name SEPARATOR ', ') AS assigned_types_str
        FROM pokemon_species ps
        LEFT JOIN species_type st ON ps.species_id = st.species_id
        LEFT JOIN pokemon_types pt ON st.type_id = pt.type_id
        GROUP BY ps.species_id, ps.species_name, ps.rarity
        ORDER BY ps.species_id DESC
    """
    species_list = execute_query(query)
    all_types = execute_query("SELECT type_id, type_name FROM pokemon_types ORDER BY type_name")
    
    edit_id = request.query_params.get("edit_id")
    edit_item = None
    if edit_id:
        rows = execute_query("SELECT * FROM pokemon_species WHERE species_id = %s", (edit_id,))
        if rows:
            edit_item = rows[0]
            type_rows = execute_query("SELECT type_id FROM species_type WHERE species_id = %s", (edit_id,))
            edit_item['assigned_types'] = [r['type_id'] for r in type_rows]

    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
        
    return templates.TemplateResponse("admin/species.html", {
        "request": request, 
        "species_list": species_list,
        "all_types": all_types,
        "edit_item": edit_item,
        "csrf_token": request.session["csrf_token"]
    })

@router.post("/add")
async def add_species(
    request: Request,
    species_name: str = Form(...),
    rarity: str = Form(...),
    type_ids: List[int] = Form(default=[])
):
    session_csrf = request.session.get("csrf_token")
    form_data = await request.form()
    request_csrf = form_data.get("csrf_token")
    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(request_csrf)):
        return RedirectResponse(url="/admin/species?msg=csrf_error", status_code=303)
        
    existing = execute_query(
        "SELECT species_id FROM pokemon_species WHERE LOWER(species_name) = LOWER(%s) AND rarity = %s",
        (species_name, rarity)
    )
    if existing:
        return RedirectResponse(url="/admin/species?msg=duplicate_error", status_code=303)

    try:
        execute_query(
            "INSERT INTO pokemon_species (species_name, rarity) VALUES (%s, %s)",
            (species_name, rarity)
        )
        
        if type_ids:
            rows = execute_query("SELECT species_id FROM pokemon_species WHERE species_name = %s AND rarity = %s", (species_name, rarity))
            if rows:
                new_species_id = rows[0]['species_id']
                for tid in type_ids:
                    execute_query("INSERT INTO species_type (species_id, type_id) VALUES (%s, %s)", (new_species_id, tid))
                    
    except Exception as e:
        if "Duplicate entry" in str(e):
            return RedirectResponse(url="/admin/species?msg=duplicate_error", status_code=303)
        return RedirectResponse(url="/admin/species?msg=error", status_code=303)
        
    return RedirectResponse(url="/admin/species", status_code=303)

@router.post("/delete/{species_id}")
async def delete_species(request: Request, species_id: int):
    try:
        execute_query("DELETE FROM pokemon_species WHERE species_id = %s", (species_id,))
    except Exception as e:
        return RedirectResponse(url="/admin/species?msg=in_use_error", status_code=303)
    
    return RedirectResponse(url="/admin/species", status_code=303)

@router.post("/edit/{species_id}")
async def edit_species(
    request: Request,
    species_id: int,
    species_name: str = Form(...),
    rarity: str = Form(...),
    type_ids: List[int] = Form(default=[])
):
    session_csrf = request.session.get("csrf_token")
    form_data = await request.form()
    request_csrf = form_data.get("csrf_token")
    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(request_csrf)):
        return RedirectResponse(url="/admin/species?msg=csrf_error", status_code=303)

    existing = execute_query(
        "SELECT species_id FROM pokemon_species WHERE LOWER(species_name) = LOWER(%s) AND LOWER(rarity) = LOWER(%s) AND species_id != %s",
        (species_name, rarity, species_id)
    )
    if existing:
        return RedirectResponse(url="/admin/species?msg=duplicate_error", status_code=303)

    try:
        execute_query(
            "UPDATE pokemon_species SET species_name = %s, rarity = %s WHERE species_id = %s",
            (species_name, rarity, species_id)
        )
        
        execute_query("DELETE FROM species_type WHERE species_id = %s", (species_id,))
        for tid in type_ids:
            execute_query("INSERT INTO species_type (species_id, type_id) VALUES (%s, %s)", (species_id, tid))
            
    except Exception as e:
        if "Duplicate entry" in str(e):
            return RedirectResponse(url="/admin/species?msg=duplicate_error", status_code=303)
        return RedirectResponse(url="/admin/species?msg=error", status_code=303)
        
    return RedirectResponse(url="/admin/species", status_code=303)
