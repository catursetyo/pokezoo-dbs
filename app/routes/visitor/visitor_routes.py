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


def get_visitor_profile(request: Request):
    user_id = request.session.get("user_id")
    rows = execute_query(
        "SELECT visitor_id, name FROM visitors WHERE user_id = %s",
        (user_id,)
    )
    return rows[0] if rows else None


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    visitor = get_visitor_profile(request)

    if not visitor:
        return HTMLResponse("Visitor profile not found.", status_code=404)

    tickets = execute_query("""
        SELECT ticket_id, visit_date, ticket_type, price, status
        FROM tickets
        WHERE visitor_id = %s
        ORDER BY visit_date DESC
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
    habitats = execute_query("""
        SELECT
            h.habitat_id,
            h.habitat_name,
            h.habitat_type,
            h.capacity,
            h.status,
            COUNT(p.pokemon_id) AS pop
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
        "habitats": habitats
    })


@router.get("/habitats/{habitat_id}", response_class=HTMLResponse)
async def habitat_detail(request: Request, habitat_id: int):
    visitor = get_visitor_profile(request)

    if not visitor:
        return HTMLResponse("Visitor profile not found.", status_code=404)

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

    active_tickets = execute_query("""
        SELECT ticket_id, visit_date, ticket_type, status
        FROM tickets
        WHERE visitor_id = %s
          AND status = 'active'
        ORDER BY visit_date DESC
    """, (visitor["visitor_id"],))

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

    ticket_rows = execute_query("""
        SELECT ticket_id
        FROM tickets
        WHERE ticket_id = %s
          AND visitor_id = %s
          AND status = 'active'
    """, (ticket_id, visitor["visitor_id"]))

    if not ticket_rows:
        return RedirectResponse(url="/visitor/explore?msg=invalid_ticket", status_code=303)

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

    habitat_id = pokemon_rows[0]["habitat_id"]

    execute_query("""
        INSERT INTO pokemon_interactions
            (ticket_id, pokemon_id, interaction_type, interaction_time, notes)
        VALUES
            (%s, %s, %s, NOW(), %s)
    """, (ticket_id, pokemon_id, interaction_type, notes))

    return RedirectResponse(
        url=f"/visitor/habitats/{habitat_id}?msg=interaction_success",
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

    price = 25.00 if ticket_type == "General Admission" else 75.00

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
    comment: str = Form(...),
    favorite_habitat: str = Form(...)
):
    visitor = get_visitor_profile(request)

    if not visitor:
        return HTMLResponse("Visitor profile not found.", status_code=404)

    db = await get_mongo_db()
    reviews_col = db["visitor_reviews"]

    review_doc = {
        "visitor_id": visitor["visitor_id"],
        "rating": rating,
        "comment": comment,
        "favorite_habitat": favorite_habitat,
        "date_submitted": datetime.utcnow().isoformat()
    }

    await reviews_col.insert_one(review_doc)

    return RedirectResponse(url="/visitor/dashboard?msg=review_submitted", status_code=303)
