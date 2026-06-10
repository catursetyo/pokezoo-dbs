from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ...database import execute_query, get_mongo_db
from ...main import require_role

import secrets

router = APIRouter(dependencies=[Depends(require_role(["keeper"]))])
templates = Jinja2Templates(directory="app/templates")


def get_pokemon_map(pokemon_ids):
    clean_ids = []

    for pokemon_id in pokemon_ids:
        if pokemon_id is None:
            continue

        try:
            clean_ids.append(int(pokemon_id))
        except (ValueError, TypeError):
            continue

    clean_ids = list(set(clean_ids))

    if not clean_ids:
        return {}

    placeholders = ", ".join(["%s"] * len(clean_ids))

    rows = execute_query(f"""
        SELECT
            p.pokemon_id,
            p.nickname,
            ps.species_name
        FROM pokemon p
        JOIN pokemon_species ps ON p.species_id = ps.species_id
        WHERE p.pokemon_id IN ({placeholders})
    """, tuple(clean_ids))

    return {
        row["pokemon_id"]: row
        for row in rows
    }


def get_habitat_map(habitat_ids):
    clean_ids = []

    for habitat_id in habitat_ids:
        if habitat_id is None:
            continue

        try:
            clean_ids.append(int(habitat_id))
        except (ValueError, TypeError):
            continue

    clean_ids = list(set(clean_ids))

    if not clean_ids:
        return {}

    placeholders = ", ".join(["%s"] * len(clean_ids))

    rows = execute_query(f"""
        SELECT habitat_id, habitat_name
        FROM habitats
        WHERE habitat_id IN ({placeholders})
    """, tuple(clean_ids))

    return {
        row["habitat_id"]: row
        for row in rows
    }


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user_id = request.session.get("user_id")

    keeper_row = execute_query(
        "SELECT keeper_id, name, shift FROM keepers WHERE user_id = %s",
        (user_id,)
    )

    if not keeper_row:
        return HTMLResponse("Keeper profile not found. Please contact admin.", status_code=404)

    keeper = keeper_row[0]
    keeper_id = keeper["keeper_id"]

    assigned_pokemon = execute_query("""
        SELECT
            p.pokemon_id,
            p.nickname,
            s.species_name,
            p.health_status,
            pk.assigned_since
        FROM pokemon p
        JOIN pokemon_species s ON p.species_id = s.species_id
        JOIN pokemon_keepers pk ON p.pokemon_id = pk.pokemon_id
        WHERE pk.keeper_id = %s
        ORDER BY s.species_name, p.nickname
    """, (keeper_id,))

    schedules = execute_query("""
        SELECT
            fs.feeding_id,
            p.nickname,
            ps.species_name,
            f.food_name,
            fs.feeding_time,
            fs.status
        FROM feeding_schedules fs
        JOIN pokemon p ON fs.pokemon_id = p.pokemon_id
        JOIN pokemon_species ps ON p.species_id = ps.species_id
        JOIN foods f ON fs.food_id = f.food_id
        WHERE fs.keeper_id = %s
          AND fs.status = 'scheduled'
        ORDER BY fs.feeding_time ASC
    """, (keeper_id,))

    feeding_history = execute_query("""
        SELECT
            fs.feeding_id,
            p.nickname,
            ps.species_name,
            f.food_name,
            fs.feeding_time,
            fs.status
        FROM feeding_schedules fs
        JOIN pokemon p ON fs.pokemon_id = p.pokemon_id
        JOIN pokemon_species ps ON p.species_id = ps.species_id
        JOIN foods f ON fs.food_id = f.food_id
        WHERE fs.keeper_id = %s
          AND fs.status IN ('completed', 'missed')
        ORDER BY fs.feeding_time DESC
        LIMIT 10
    """, (keeper_id,))

    db = await get_mongo_db()

    behavior_logs = await db["pokemon_behavior_logs"].find({
        "keeper_user_id": {"$in": [user_id, str(user_id)]}
    }).sort([
        ("date", -1),
        ("time", -1)
    ]).to_list(length=10)

    incident_reports = await db["incident_reports"].find({
        "keeper_user_id": {"$in": [user_id, str(user_id)]}
    }).sort("date_reported", -1).to_list(length=10)

    behavior_pokemon_ids = [
        log.get("pokemon_id")
        for log in behavior_logs
    ]

    incident_pokemon_ids = [
        incident.get("pokemon_id")
        for incident in incident_reports
        if incident.get("pokemon_id") is not None
    ]

    incident_habitat_ids = [
        incident.get("habitat_id")
        for incident in incident_reports
        if incident.get("habitat_id") is not None
    ]

    pokemon_map = get_pokemon_map(behavior_pokemon_ids + incident_pokemon_ids)
    habitat_map = get_habitat_map(incident_habitat_ids)

    for log in behavior_logs:
        log["_id"] = str(log["_id"])

        try:
            pokemon_id = int(log.get("pokemon_id"))
        except (ValueError, TypeError):
            pokemon_id = None

        pokemon = pokemon_map.get(pokemon_id)

        if pokemon:
            log["pokemon_name"] = pokemon["nickname"] or pokemon["species_name"]
            log["species_name"] = pokemon["species_name"]
        else:
            log["pokemon_name"] = f"Pokémon #{log.get('pokemon_id')}"
            log["species_name"] = "Unknown"

    for incident in incident_reports:
        incident["_id"] = str(incident["_id"])

        try:
            pokemon_id = int(incident.get("pokemon_id")) if incident.get("pokemon_id") is not None else None
        except (ValueError, TypeError):
            pokemon_id = None

        try:
            habitat_id = int(incident.get("habitat_id")) if incident.get("habitat_id") is not None else None
        except (ValueError, TypeError):
            habitat_id = None

        pokemon = pokemon_map.get(pokemon_id)
        habitat = habitat_map.get(habitat_id)

        if pokemon:
            incident["pokemon_name"] = pokemon["nickname"] or pokemon["species_name"]
            incident["species_name"] = pokemon["species_name"]
        else:
            incident["pokemon_name"] = "No specific Pokémon"

        if habitat:
            incident["habitat_name"] = habitat["habitat_name"]
        else:
            incident["habitat_name"] = "Unknown Habitat"

        if isinstance(incident.get("actions_taken"), list):
            incident["actions_taken_text"] = ", ".join(incident["actions_taken"])
        else:
            incident["actions_taken_text"] = incident.get("actions_taken", "")

    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)

    return templates.TemplateResponse("keeper/dashboard.html", {
        "request": request,
        "keeper": keeper,
        "assigned_pokemon": assigned_pokemon,
        "schedules": schedules,
        "feeding_history": feeding_history,
        "behavior_logs": behavior_logs,
        "incident_reports": incident_reports,
        "csrf_token": request.session["csrf_token"]
    })


@router.post("/feedings/update/{feeding_id}")
async def update_feeding(request: Request, feeding_id: int, status: str = Form(...)):
    user_id = request.session.get("user_id")

    keeper_row = execute_query(
        "SELECT keeper_id FROM keepers WHERE user_id = %s",
        (user_id,)
    )

    if keeper_row:
        keeper_id = keeper_row[0]["keeper_id"]

        try:
            execute_query("""
                UPDATE feeding_schedules
                SET status = %s
                WHERE feeding_id = %s AND keeper_id = %s
            """, (status, feeding_id, keeper_id))
        except Exception:
            return RedirectResponse(
                url="/keeper/dashboard?msg=stock_error",
                status_code=303
            )

    return RedirectResponse(url="/keeper/dashboard", status_code=303)
