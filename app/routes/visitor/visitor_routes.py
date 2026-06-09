from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ...database import execute_query, get_mongo_db
from ...main import require_role
import secrets
from datetime import datetime

router = APIRouter(dependencies=[Depends(require_role(["visitor"]))])
templates = Jinja2Templates(directory="app/templates")

ALLOWED_INTERACTIONS = {"photo", "feeding", "show", "battle_event"}

TICKET_PRICES = {
    "Student": 10.00,
    "General Admission": 25.00,
    "VIP Pass": 75.00,
}

TICKET_MAX_USES_CASE = """
CASE
    WHEN t.ticket_type = 'VIP Pass' THEN 5
    WHEN t.ticket_type = 'General Admission' THEN 2
    WHEN t.ticket_type = 'Student' THEN 1
    ELSE 1
END
"""


def get_visitor_profile(request: Request):
    user_id = request.session.get("user_id")
    rows = execute_query(
        "SELECT visitor_id, name FROM visitors WHERE user_id = %s",
        (user_id,)
    )
    return rows[0] if rows else None


def get_active_tickets(visitor_id: int):
    return execute_query(f"""
        SELECT *
        FROM (
            SELECT
                t.ticket_id,
                t.visit_date,
                t.ticket_type,
                t.status,
                COUNT(pi.interaction_id) AS used_count,
                {TICKET_MAX_USES_CASE} AS max_uses,
                GREATEST(({TICKET_MAX_USES_CASE}) - COUNT(pi.interaction_id), 0) AS remaining_uses
            FROM tickets t
            LEFT JOIN pokemon_interactions pi
                ON t.ticket_id = pi.ticket_id
            WHERE t.visitor_id = %s
              AND t.status = 'active'
            GROUP BY
                t.ticket_id,
                t.visit_date,
                t.ticket_type,
                t.status
        ) ticket_usage
        WHERE remaining_uses > 0
        ORDER BY visit_date DESC, ticket_id DESC
    """, (visitor_id,))


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    visitor = get_visitor_profile(request)

    if not visitor:
        return HTMLResponse("Visitor profile not found.", status_code=404)

    tickets = execute_query(f"""
        SELECT
            t.ticket_id,
            t.visit_date,
            t.ticket_type,
            t.price,
            t.status,
            COUNT(pi.interaction_id) AS used_count,
            {TICKET_MAX_USES_CASE} AS max_uses,
            GREATEST(({TICKET_MAX_USES_CASE}) - COUNT(pi.interaction_id), 0) AS remaining_uses
        FROM tickets t
        LEFT JOIN pokemon_interactions pi
            ON t.ticket_id = pi.ticket_id
        WHERE t.visitor_id = %s
        GROUP BY
            t.ticket_id,
            t.visit_date,
            t.ticket_type,
            t.price,
            t.status
        ORDER BY t.visit_date DESC, t.ticket_id DESC
    """, (visitor["visitor_id"],))

    interactions = execute_query("""
        SELECT
            pi.interaction_id,
            pi.interaction_type,
            pi.interaction_time,
            pi.notes,
            t.ticket_id,
            t.visit_date,
            p.nickname,
            ps.species_name,
            ps.rarity,
            h.habitat_name,
            GROUP_CONCAT(DISTINCT pt.type_name ORDER BY pt.type_name SEPARATOR ', ') AS types_str
        FROM pokemon_interactions pi
        JOIN tickets t ON pi.ticket_id = t.ticket_id
        JOIN pokemon p ON pi.pokemon_id = p.pokemon_id
        JOIN pokemon_species ps ON p.species_id = ps.species_id
        LEFT JOIN habitats h ON p.habitat_id = h.habitat_id
        LEFT JOIN species_type st ON ps.species_id = st.species_id
        LEFT JOIN pokemon_types pt ON st.type_id = pt.type_id
        WHERE t.visitor_id = %s
        GROUP BY
            pi.interaction_id,
            pi.interaction_type,
            pi.interaction_time,
            pi.notes,
            t.ticket_id,
            t.visit_date,
            p.nickname,
            ps.species_name,
            ps.rarity,
            h.habitat_name
        ORDER BY pi.interaction_time DESC
        LIMIT 20
    """, (visitor["visitor_id"],))

    return templates.TemplateResponse("visitor/dashboard.html", {
        "request": request,
        "visitor": visitor,
        "tickets": tickets,
        "interactions": interactions
    })


@router.get("/explore", response_class=HTMLResponse)
async def explore(request: Request):
    visitor = get_visitor_profile(request)

    if not visitor:
        return HTMLResponse("Visitor profile not found.", status_code=404)

    active_tickets = get_active_tickets(visitor["visitor_id"])

    if not active_tickets:
        return RedirectResponse(
            url="/visitor/tickets/buy?msg=no_active_ticket",
            status_code=303
        )

    habitats = execute_query("""
        SELECT
            h.habitat_id,
            h.habitat_name,
            h.habitat_type,
            h.capacity,
            h.status,
            COUNT(p.pokemon_id) AS population_count
        FROM habitats h
        LEFT JOIN pokemon p
            ON h.habitat_id = p.habitat_id
            AND p.status = 'active'
        WHERE h.status = 'active'
        GROUP BY
            h.habitat_id,
            h.habitat_name,
            h.habitat_type,
            h.capacity,
            h.status
        ORDER BY h.habitat_name
    """)

    return templates.TemplateResponse("visitor/explore.html", {
        "request": request,
        "visitor": visitor,
        "habitats": habitats,
        "active_tickets": active_tickets
    })


@router.get("/habitats/{habitat_id}", response_class=HTMLResponse)
async def habitat_detail(request: Request, habitat_id: int):
    visitor = get_visitor_profile(request)

    if not visitor:
        return HTMLResponse("Visitor profile not found.", status_code=404)

    active_tickets = get_active_tickets(visitor["visitor_id"])

    if not active_tickets:
        return RedirectResponse(
            url="/visitor/tickets/buy?msg=no_active_ticket",
            status_code=303
        )

    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)

    habitat_rows = execute_query("""
        SELECT habitat_id, habitat_name, habitat_type, capacity, status
        FROM habitats
        WHERE habitat_id = %s AND status = 'active'
    """, (habitat_id,))

    if not habitat_rows:
        return HTMLResponse("Habitat not found or inactive.", status_code=404)

    habitat = habitat_rows[0]

    pokemon_list = execute_query("""
        SELECT
            p.pokemon_id,
            p.nickname,
            p.health_status,
            p.status,
            ps.species_name,
            ps.rarity,
            GROUP_CONCAT(DISTINCT pt.type_name ORDER BY pt.type_name SEPARATOR ', ') AS types_str
        FROM pokemon p
        JOIN pokemon_species ps ON p.species_id = ps.species_id
        LEFT JOIN species_type st ON ps.species_id = st.species_id
        LEFT JOIN pokemon_types pt ON st.type_id = pt.type_id
        WHERE p.habitat_id = %s
          AND p.status = 'active'
        GROUP BY
            p.pokemon_id,
            p.nickname,
            p.health_status,
            p.status,
            ps.species_name,
            ps.rarity
        ORDER BY ps.species_name, p.nickname
    """, (habitat_id,))

    return templates.TemplateResponse("visitor/habitat_detail.html", {
        "request": request,
        "visitor": visitor,
        "habitat": habitat,
        "pokemon_list": pokemon_list,
        "active_tickets": active_tickets,
        "csrf_token": request.session["csrf_token"]
    })


@router.post("/interactions/add")
async def add_interaction(
    request: Request,
    csrf_token: str = Form(...),
    ticket_id: int = Form(...),
    pokemon_id: int = Form(...),
    interaction_type: str = Form(...),
    notes: str = Form("")
):
    session_csrf = request.session.get("csrf_token")

    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(csrf_token)):
        return RedirectResponse(url="/visitor/explore?msg=csrf_error", status_code=303)

    visitor = get_visitor_profile(request)

    if not visitor:
        return HTMLResponse("Visitor profile not found.", status_code=404)

    if interaction_type not in ALLOWED_INTERACTIONS:
        return RedirectResponse(url="/visitor/explore?msg=invalid_interaction", status_code=303)

    ticket_rows = execute_query(f"""
        SELECT *
        FROM (
            SELECT
                t.ticket_id,
                t.ticket_type,
                COUNT(pi.interaction_id) AS used_count,
                {TICKET_MAX_USES_CASE} AS max_uses
            FROM tickets t
            LEFT JOIN pokemon_interactions pi
                ON t.ticket_id = pi.ticket_id
            WHERE t.ticket_id = %s
              AND t.visitor_id = %s
              AND t.status = 'active'
            GROUP BY
                t.ticket_id,
                t.ticket_type
        ) ticket_usage
        WHERE used_count < max_uses
    """, (ticket_id, visitor["visitor_id"]))

    if not ticket_rows:
        return RedirectResponse(
            url="/visitor/tickets/buy?msg=no_active_ticket",
            status_code=303
        )

    pokemon_rows = execute_query("""
        SELECT p.pokemon_id, p.habitat_id
        FROM pokemon p
        JOIN habitats h ON p.habitat_id = h.habitat_id
        WHERE p.pokemon_id = %s
          AND p.status = 'active'
          AND h.status = 'active'
    """, (pokemon_id,))

    if not pokemon_rows:
        return RedirectResponse(url="/visitor/explore?msg=invalid_pokemon", status_code=303)

    execute_query("""
        INSERT INTO pokemon_interactions
            (ticket_id, pokemon_id, interaction_type, interaction_time, notes)
        VALUES
            (%s, %s, %s, NOW(), %s)
    """, (ticket_id, pokemon_id, interaction_type, notes))

    usage_rows = execute_query(f"""
        SELECT
            COUNT(pi.interaction_id) AS used_count,
            {TICKET_MAX_USES_CASE} AS max_uses
        FROM tickets t
        LEFT JOIN pokemon_interactions pi
            ON t.ticket_id = pi.ticket_id
        WHERE t.ticket_id = %s
          AND t.visitor_id = %s
        GROUP BY
            t.ticket_id,
            t.ticket_type
    """, (ticket_id, visitor["visitor_id"]))

    if usage_rows:
        used_count = int(usage_rows[0]["used_count"])
        max_uses = int(usage_rows[0]["max_uses"])

        if used_count >= max_uses:
            execute_query("""
                UPDATE tickets
                SET status = 'used'
                WHERE ticket_id = %s
                  AND visitor_id = %s
                  AND status = 'active'
            """, (ticket_id, visitor["visitor_id"]))

    return RedirectResponse(
        url="/visitor/dashboard?msg=interaction_success",
        status_code=303
    )


@router.get("/tickets/buy", response_class=HTMLResponse)
async def buy_tickets_page(request: Request):
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)

    return templates.TemplateResponse("visitor/buy_tickets.html", {
        "request": request,
        "csrf_token": request.session["csrf_token"]
    })


@router.post("/tickets/buy")
async def buy_tickets(
    request: Request,
    visit_date: str = Form(...),
    ticket_type: str = Form(...),
    payment_method: str = Form(...)
):
    visitor = get_visitor_profile(request)

    if not visitor:
        return HTMLResponse("Visitor profile not found.", status_code=404)

    if ticket_type not in TICKET_PRICES:
        return RedirectResponse(
            url="/visitor/tickets/buy?msg=invalid_ticket_type",
            status_code=303
        )

    price = TICKET_PRICES[ticket_type]

    execute_query("""
        INSERT INTO tickets
            (visitor_id, visit_date, ticket_type, payment_method, purchase_date, price)
        VALUES
            (%s, %s, %s, %s, NOW(), %s)
    """, (visitor["visitor_id"], visit_date, ticket_type, payment_method, price))

    return RedirectResponse(url="/visitor/dashboard", status_code=303)


@router.get("/reviews", response_class=HTMLResponse)
async def get_reviews_page(request: Request):
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)

    return templates.TemplateResponse("visitor/reviews.html", {
        "request": request,
        "csrf_token": request.session["csrf_token"]
    })


@router.post("/reviews")
async def create_review(
    request: Request,
    rating: int = Form(...),
    comment: str = Form(""),
    favorite_habitat: str = Form(...)
):
    user_id = request.session.get("user_id")
    visitor = execute_query(
        "SELECT visitor_id FROM visitors WHERE user_id = %s",
        (user_id,)
    )[0]

    db = await get_mongo_db()
    reviews_col = db["visitor_reviews"]

    review_doc = {
        "visitor_id": visitor["visitor_id"],
        "rating": rating,
        "comment": comment.strip() if comment else "",
        "favorite_habitat": favorite_habitat,
        "date_submitted": datetime.utcnow().isoformat()
    }

    await reviews_col.insert_one(review_doc)

    return RedirectResponse(url="/visitor/dashboard?msg=review_submitted", status_code=303)
