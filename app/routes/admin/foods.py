from ...main import require_role
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ...database import execute_query
import secrets

router = APIRouter(dependencies=[Depends(require_role(["admin"]))])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_foods(request: Request):
    foods_list = execute_query("SELECT food_id, food_name, nutrition, stock FROM foods ORDER BY food_name")
    
    edit_id = request.query_params.get("edit_id")
    edit_item = None
    if edit_id:
        rows = execute_query("SELECT * FROM foods WHERE food_id = %s", (edit_id,))
        if rows:
            edit_item = rows[0]

    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
        
    return templates.TemplateResponse("admin/foods.html", {
        "request": request, 
        "foods_list": foods_list,
        "edit_item": edit_item,
        "csrf_token": request.session["csrf_token"]
    })

@router.post("/add")
async def add_food(
    request: Request,
    food_name: str = Form(...),
    nutrition: str = Form(""),
    stock: int = Form(0)
):
    session_csrf = request.session.get("csrf_token")
    form_data = await request.form()
    request_csrf = form_data.get("csrf_token")
    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(request_csrf)):
        return RedirectResponse(url="/admin/foods?msg=csrf_error", status_code=303)

    # Check for duplicate
    existing = execute_query("SELECT food_id FROM foods WHERE LOWER(food_name) = LOWER(%s)", (food_name,))
    if existing:
        return RedirectResponse(url="/admin/foods?msg=duplicate_error", status_code=303)

    try:
        execute_query(
            "INSERT INTO foods (food_name, nutrition, stock) VALUES (%s, %s, %s)",
            (food_name, nutrition, stock)
        )
    except Exception as e:
        return RedirectResponse(url="/admin/foods?msg=error", status_code=303)
        
    return RedirectResponse(url="/admin/foods", status_code=303)

@router.post("/restock/{food_id}")
async def restock_food(request: Request, food_id: int, amount: int = Form(...)):
    execute_query("UPDATE foods SET stock = stock + %s WHERE food_id = %s", (amount, food_id))
    return RedirectResponse(url="/admin/foods", status_code=303)

@router.post("/delete/{food_id}")
async def delete_food(request: Request, food_id: int):
    try:
        execute_query("DELETE FROM foods WHERE food_id = %s", (food_id,))
    except Exception as e:
        return RedirectResponse(url="/admin/foods?msg=in_use_error", status_code=303)
    
    return RedirectResponse(url="/admin/foods", status_code=303)

@router.post("/edit/{food_id}")
async def edit_food(
    request: Request,
    food_id: int,
    food_name: str = Form(...),
    nutrition: str = Form(""),
    stock: int = Form(0)
):
    session_csrf = request.session.get("csrf_token")
    form_data = await request.form()
    request_csrf = form_data.get("csrf_token")
    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(request_csrf)):
        return RedirectResponse(url="/admin/foods?msg=csrf_error", status_code=303)

    # Check for duplicate
    existing = execute_query(
        "SELECT food_id FROM foods WHERE LOWER(food_name) = LOWER(%s) AND food_id != %s", 
        (food_name, food_id)
    )
    if existing:
        return RedirectResponse(url="/admin/foods?msg=duplicate_error", status_code=303)

    try:
        execute_query(
            "UPDATE foods SET food_name = %s, nutrition = %s, stock = %s WHERE food_id = %s",
            (food_name, nutrition, stock, food_id)
        )
    except Exception as e:
        return RedirectResponse(url="/admin/foods?msg=error", status_code=303)
        
    return RedirectResponse(url="/admin/foods", status_code=303)
