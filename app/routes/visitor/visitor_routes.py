from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ...database import execute_query, get_mongo_db
from ...main import require_role
import secrets
from datetime import datetime

router = APIRouter(dependencies=[Depends(require_role(["visitor"]))])
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user_id = request.session.get("user_id")
    visitor_row = execute_query("SELECT visitor_id, name FROM visitors WHERE user_id = %s", (user_id,))
    if not visitor_row:
        return HTMLResponse("Visitor profile not found.", status_code=404)
        
    visitor = visitor_row[0]
    
    tickets = execute_query("""
        SELECT ticket_id, visit_date, ticket_type, price, status
        FROM tickets
        WHERE visitor_id = %s
        ORDER BY visit_date DESC
    """, (visitor['visitor_id'],))
    
    return templates.TemplateResponse("visitor/dashboard.html", {
        "request": request,
        "visitor": visitor,
        "tickets": tickets
    })

@router.get("/explore", response_class=HTMLResponse)
async def explore(request: Request):
    habitats = execute_query("""
        SELECT h.habitat_name, h.habitat_type, COUNT(p.pokemon_id) as pop
        FROM habitats h
        LEFT JOIN pokemon p ON h.habitat_id = p.habitat_id AND p.status = 'active'
        WHERE h.status = 'active'
        GROUP BY h.habitat_id
    """)
    
    return templates.TemplateResponse("visitor/explore.html", {
        "request": request,
        "habitats": habitats
    })

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
    user_id = request.session.get("user_id")
    visitor = execute_query("SELECT visitor_id FROM visitors WHERE user_id = %s", (user_id,))[0]
    
    price = 25.00 if ticket_type == 'General Admission' else 75.00
    
    execute_query("""
        INSERT INTO tickets (visitor_id, visit_date, ticket_type, payment_method, purchase_date, price)
        VALUES (%s, %s, %s, %s, NOW(), %s)
    """, (visitor['visitor_id'], visit_date, ticket_type, payment_method, price))
    
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
    user_id = request.session.get("user_id")
    visitor = execute_query("SELECT visitor_id FROM visitors WHERE user_id = %s", (user_id,))[0]
    
    db = await get_mongo_db()
    reviews_col = db["visitor_reviews"]
    
    review_doc = {
        "visitor_id": visitor['visitor_id'],
        "rating": rating,
        "comment": comment,
        "favorite_habitat": favorite_habitat,
        "date_submitted": datetime.utcnow().isoformat()
    }
    
    await reviews_col.insert_one(review_doc)
    return RedirectResponse(url="/visitor/dashboard?msg=review_submitted", status_code=303)
