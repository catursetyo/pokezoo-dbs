from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ...database import execute_query, mysql_transaction
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

    habitats = execute_query("""
        SELECT habitat_id, habitat_name
        FROM habitats
        WHERE status = 'active'
        ORDER BY habitat_name
    """)

    keepers = execute_query("""
        SELECT keeper_id, name, shift
        FROM keepers
        ORDER BY name
    """)

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
            edit_item["keeper_ids"] = (
                [int(x) for x in edit_item["keeper_ids_str"].split(",")]
                if edit_item["keeper_ids_str"]
                else []
            )

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

    habitat_info = execute_query("""
        SELECT
            capacity,
            (
                SELECT COUNT(*)
                FROM pokemon
                WHERE habitat_id = %s
                  AND status = 'active'
            ) AS current_count
        FROM habitats
        WHERE habitat_id = %s
    """, (habitat_id, habitat_id))

    if habitat_info and habitat_info[0]["current_count"] >= habitat_info[0]["capacity"]:
        return RedirectResponse(url="/admin/pokemon?msg=capacity_error", status_code=303)

    existing = execute_query(
        "SELECT pokemon_id FROM pokemon WHERE LOWER(nickname) = LOWER(%s)",
        (nickname,)
    )

    if existing:
        return RedirectResponse(url="/admin/pokemon?msg=duplicate_error", status_code=303)

    try:
        with mysql_transaction() as cursor:
            cursor.execute("""
                INSERT INTO pokemon (species_id, habitat_id, nickname, entry_date)
                VALUES (%s, %s, %s, CURDATE())
            """, (species_id, habitat_id, nickname))

            new_poke_id = cursor.lastrowid

            for keeper_id in keeper_ids:
                cursor.execute("""
                    INSERT INTO pokemon_keepers
                        (pokemon_id, keeper_id, assigned_since)
                    VALUES
                        (%s, %s, CURDATE())
                """, (new_poke_id, keeper_id))

            cursor.execute("""
                INSERT INTO pokemon_health_history
                    (pokemon_id, old_health_status, new_health_status, changed_by, change_reason)
                VALUES
                    (%s, NULL, 'healthy', %s, %s)
            """, (
                new_poke_id,
                request.session.get("user_id"),
                "Initial health status when Pokémon was added to the zoo"
            ))

    except Exception as e:
        if "Duplicate entry" in str(e):
            return RedirectResponse(url="/admin/pokemon?msg=duplicate_error", status_code=303)

        return RedirectResponse(url="/admin/pokemon?msg=error", status_code=303)

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
    health_note: str = Form(""),
    keeper_ids: List[int] = Form(default=[])
):
    session_csrf = request.session.get("csrf_token")
    form_data = await request.form()
    request_csrf = form_data.get("csrf_token")

    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(request_csrf)):
        return RedirectResponse(url="/admin/pokemon?msg=csrf_error", status_code=303)

    if not keeper_ids:
        return RedirectResponse(url="/admin/pokemon?msg=keeper_required_error", status_code=303)

    old_poke = execute_query("""
        SELECT habitat_id, health_status
        FROM pokemon
        WHERE pokemon_id = %s
    """, (pokemon_id,))

    if not old_poke:
        return RedirectResponse(url="/admin/pokemon?msg=not_found", status_code=303)

    old_habitat_id = old_poke[0]["habitat_id"]
    old_health_status = old_poke[0]["health_status"]

    if old_habitat_id != habitat_id:
        habitat_info = execute_query("""
            SELECT
                capacity,
                (
                    SELECT COUNT(*)
                    FROM pokemon
                    WHERE habitat_id = %s
                      AND status = 'active'
                ) AS current_count
            FROM habitats
            WHERE habitat_id = %s
        """, (habitat_id, habitat_id))

        if habitat_info and habitat_info[0]["current_count"] >= habitat_info[0]["capacity"]:
            return RedirectResponse(url="/admin/pokemon?msg=capacity_error", status_code=303)

    existing = execute_query(
        """
        SELECT pokemon_id
        FROM pokemon
        WHERE LOWER(nickname) = LOWER(%s)
          AND pokemon_id != %s
        """,
        (nickname, pokemon_id)
    )

    if existing:
        return RedirectResponse(url="/admin/pokemon?msg=duplicate_error", status_code=303)

    try:
        with mysql_transaction() as cursor:
            cursor.execute("""
                UPDATE pokemon 
                SET
                    species_id = %s,
                    habitat_id = %s,
                    nickname = %s,
                    health_status = %s,
                    status = %s
                WHERE pokemon_id = %s
            """, (
                species_id,
                habitat_id,
                nickname,
                health_status,
                status,
                pokemon_id
            ))

            cursor.execute(
                "DELETE FROM pokemon_keepers WHERE pokemon_id = %s",
                (pokemon_id,)
            )

            for keeper_id in keeper_ids:
                cursor.execute("""
                    INSERT INTO pokemon_keepers
                        (pokemon_id, keeper_id, assigned_since)
                    VALUES
                        (%s, %s, CURDATE())
                """, (pokemon_id, keeper_id))

            if old_health_status != health_status:
                cursor.execute("""
                    INSERT INTO pokemon_health_history
                        (pokemon_id, old_health_status, new_health_status, changed_by, change_reason)
                    VALUES
                        (%s, %s, %s, %s, %s)
                """, (
                    pokemon_id,
                    old_health_status,
                    health_status,
                    request.session.get("user_id"),
                    health_note.strip() if health_note else None
                ))

    except Exception as e:
        if "Duplicate entry" in str(e):
            return RedirectResponse(url="/admin/pokemon?msg=duplicate_error", status_code=303)

        return RedirectResponse(url="/admin/pokemon?msg=error", status_code=303)

    return RedirectResponse(url="/admin/pokemon", status_code=303)


@router.get("/health-lifecycle", response_class=HTMLResponse)
async def health_lifecycle(request: Request):
    histories = execute_query("""
        SELECT
            phh.history_id,
            phh.pokemon_id,
            p.nickname,
            ps.species_name,
            phh.old_health_status,
            phh.new_health_status,
            phh.change_reason,
            phh.changed_at,
            u.username AS changed_by_username
        FROM pokemon_health_history phh
        JOIN pokemon p ON phh.pokemon_id = p.pokemon_id
        JOIN pokemon_species ps ON p.species_id = ps.species_id
        LEFT JOIN users u ON phh.changed_by = u.user_id
        ORDER BY phh.changed_at DESC
        LIMIT 100
    """)

    summary = execute_query("""
        SELECT
            health_status,
            COUNT(*) AS total
        FROM pokemon
        GROUP BY health_status
        ORDER BY total DESC
    """)

    return templates.TemplateResponse("admin/health_lifecycle.html", {
        "request": request,
        "histories": histories,
        "summary": summary
    })
