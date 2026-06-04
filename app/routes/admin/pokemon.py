from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ...database import execute_query
from ...main import require_role
import secrets
from typing import List

router = APIRouter(dependencies=[Depends(require_role(["admin"]))])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_pokemon(request: Request):
    query = """
    SELECT 
        p.pokemon_id,
        p.nickname,
        s.species_name,
        s.rarity,
        h.habitat_name,
        p.health_status,
        p.status,
        GROUP_CONCAT(DISTINCT pt.type_name ORDER BY pt.type_name SEPARATOR ', ') AS types_str,
        GROUP_CONCAT(DISTINCT k.name ORDER BY k.name SEPARATOR ', ') AS keepers_str
    FROM pokemon p
    JOIN pokemon_species s ON p.species_id = s.species_id
    LEFT JOIN habitats h ON p.habitat_id = h.habitat_id
    LEFT JOIN species_type st ON s.species_id = st.species_id
    LEFT JOIN pokemon_types pt ON st.type_id = pt.type_id
    LEFT JOIN pokemon_keepers pk ON p.pokemon_id = pk.pokemon_id
    LEFT JOIN keepers k ON pk.keeper_id = k.keeper_id
    GROUP BY 
        p.pokemon_id,
        p.nickname,
        s.species_name,
        s.rarity,
        h.habitat_name,
        p.health_status,
        p.status
    ORDER BY p.pokemon_id DESC
    """
    pokemon_list = execute_query(query)
    
    species = execute_query("""
        SELECT 
            ps.species_id, 
            ps.species_name, 
            ps.rarity,
            GROUP_CONCAT(pt.type_name ORDER BY pt.type_name SEPARATOR ', ') AS types_str
        FROM pokemon_species ps
        LEFT JOIN species_type st ON ps.species_id = st.species_id
        LEFT JOIN pokemon_types pt ON st.type_id = pt.type_id
        GROUP BY ps.species_id, ps.species_name, ps.rarity
        ORDER BY ps.species_name
    """)
    habitats = execute_query("SELECT habitat_id, habitat_name FROM habitats WHERE status = 'active'")
    keepers = execute_query("SELECT keeper_id, name, shift FROM keepers")
    
    edit_id = request.query_params.get("edit_id")
    edit_item = None
    if edit_id:
        item_query = """
            SELECT p.*, GROUP_CONCAT(pk.keeper_id) AS keeper_ids_str
            FROM pokemon p 
            LEFT JOIN pokemon_keepers pk ON p.pokemon_id = pk.pokemon_id 
            WHERE p.pokemon_id = %s
            GROUP BY p.pokemon_id
        """
        rows = execute_query(item_query, (edit_id,))
        if rows:
            edit_item = rows[0]
            edit_item['keeper_ids'] = [int(x) for x in edit_item['keeper_ids_str'].split(',')] if edit_item['keeper_ids_str'] else []

    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
        
    return templates.TemplateResponse("admin/pokemon.html", {
        "request": request, 
        "pokemon_list": pokemon_list,
        "species": species,
        "habitats": habitats,
        "keepers": keepers,
        "edit_item": edit_item,
        "csrf_token": request.session["csrf_token"]
    })

@router.post("/add")
async def add_pokemon(
    request: Request,
    nickname: str = Form(...),
    species_id: int = Form(...),
    habitat_id: int = Form(...),
    keeper_ids: List[int] = Form(default=[])
):
    session_csrf = request.session.get("csrf_token")
    form_data = await request.form()
    request_csrf = form_data.get("csrf_token")
    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(request_csrf)):
        return RedirectResponse(url="/admin/pokemon?msg=csrf_error", status_code=303)

    if not keeper_ids:
        return RedirectResponse(url="/admin/pokemon?msg=keeper_required_error", status_code=303)

    habitat_info = execute_query("SELECT capacity, (SELECT COUNT(*) FROM pokemon WHERE habitat_id = %s) as current_count FROM habitats WHERE habitat_id = %s", (habitat_id, habitat_id))
    if habitat_info and habitat_info[0]['current_count'] >= habitat_info[0]['capacity']:
        return RedirectResponse(url="/admin/pokemon?msg=capacity_error", status_code=303)

    existing = execute_query(
        "SELECT pokemon_id FROM pokemon WHERE LOWER(nickname) = LOWER(%s)",
        (nickname,)
    )
    if existing:
        return RedirectResponse(url="/admin/pokemon?msg=duplicate_error", status_code=303)

    query = """
        INSERT INTO pokemon (species_id, habitat_id, nickname, entry_date)
        VALUES (%s, %s, %s, CURDATE())
    """
    try:
        execute_query(query, (species_id, habitat_id, nickname))
    except Exception as e:
        if "Duplicate entry" in str(e):
            return RedirectResponse(url="/admin/pokemon?msg=duplicate_error", status_code=303)
        return RedirectResponse(url="/admin/pokemon?msg=error", status_code=303)
    
    if keeper_ids:
        poke_row = execute_query("SELECT pokemon_id FROM pokemon WHERE nickname = %s ORDER BY pokemon_id DESC LIMIT 1", (nickname,))
        if poke_row:
            new_poke_id = poke_row[0]['pokemon_id']
            for kid in keeper_ids:
                execute_query(
                    "INSERT INTO pokemon_keepers (pokemon_id, keeper_id, assigned_since) VALUES (%s, %s, CURDATE())", 
                    (new_poke_id, kid)
                )
            
    return RedirectResponse(url="/admin/pokemon", status_code=303)

@router.post("/delete/{pokemon_id}")
async def delete_pokemon(request: Request, pokemon_id: int):
    execute_query("DELETE FROM pokemon WHERE pokemon_id = %s", (pokemon_id,))
    return RedirectResponse(url="/admin/pokemon", status_code=303)

@router.post("/edit/{pokemon_id}")
async def edit_pokemon(
    request: Request,
    pokemon_id: int,
    nickname: str = Form(...),
    species_id: int = Form(...),
    habitat_id: int = Form(...),
    health_status: str = Form(...),
    status: str = Form(...),
    keeper_ids: List[int] = Form(default=[])
):
    session_csrf = request.session.get("csrf_token")
    form_data = await request.form()
    request_csrf = form_data.get("csrf_token")
    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(request_csrf)):
        return RedirectResponse(url="/admin/pokemon?msg=csrf_error", status_code=303)

    if not keeper_ids:
        return RedirectResponse(url="/admin/pokemon?msg=keeper_required_error", status_code=303)

    old_poke = execute_query("SELECT habitat_id FROM pokemon WHERE pokemon_id = %s", (pokemon_id,))
    if old_poke and old_poke[0]['habitat_id'] != habitat_id:
        habitat_info = execute_query("SELECT capacity, (SELECT COUNT(*) FROM pokemon WHERE habitat_id = %s) as current_count FROM habitats WHERE habitat_id = %s", (habitat_id, habitat_id))
        if habitat_info and habitat_info[0]['current_count'] >= habitat_info[0]['capacity']:
            return RedirectResponse(url="/admin/pokemon?msg=capacity_error", status_code=303)

    existing = execute_query(
        "SELECT pokemon_id FROM pokemon WHERE LOWER(nickname) = LOWER(%s) AND pokemon_id != %s",
        (nickname, pokemon_id)
    )
    if existing:
        return RedirectResponse(url="/admin/pokemon?msg=duplicate_error", status_code=303)

    query = """
        UPDATE pokemon 
        SET species_id = %s, habitat_id = %s, nickname = %s, health_status = %s, status = %s
        WHERE pokemon_id = %s
    """
    try:
        execute_query(query, (species_id, habitat_id, nickname, health_status, status, pokemon_id))
    except Exception as e:
        if "Duplicate entry" in str(e):
            return RedirectResponse(url="/admin/pokemon?msg=duplicate_error", status_code=303)
        return RedirectResponse(url="/admin/pokemon?msg=error", status_code=303)
    
    execute_query("DELETE FROM pokemon_keepers WHERE pokemon_id = %s", (pokemon_id,))
    for kid in keeper_ids:
        execute_query(
            "INSERT INTO pokemon_keepers (pokemon_id, keeper_id, assigned_since) VALUES (%s, %s, CURDATE())",
            (pokemon_id, kid)
        )
        
    return RedirectResponse(url="/admin/pokemon", status_code=303)
