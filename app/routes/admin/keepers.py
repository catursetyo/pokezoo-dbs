from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ...main import require_role
from ...database import execute_query
import secrets

router = APIRouter(dependencies=[Depends(require_role(["admin"]))])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_keepers(request: Request):
    keepers = execute_query("""
        SELECT k.keeper_id, k.name, k.shift, k.phone_number, u.username,
               COUNT(pk.pokemon_id) as assigned_count
        FROM keepers k
        JOIN users u ON k.user_id = u.user_id
        LEFT JOIN pokemon_keepers pk ON k.keeper_id = pk.keeper_id
        GROUP BY k.keeper_id, k.name, k.shift, k.phone_number, u.username
    """)
    
    edit_id = request.query_params.get("edit_id")
    edit_item = None
    if edit_id:
        rows = execute_query("""
            SELECT k.*, u.username
            FROM keepers k
            JOIN users u ON k.user_id = u.user_id
            WHERE k.keeper_id = %s
        """, (edit_id,))
        if rows:
            edit_item = rows[0]

    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
        
    return templates.TemplateResponse("admin/keepers.html", {
        "request": request, 
        "keepers": keepers,
        "edit_item": edit_item,
        "csrf_token": request.session["csrf_token"]
    })

@router.post("/add")
async def add_keeper(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    shift: str = Form(...),
    phone_number: str = Form(...)
):
    session_csrf = request.session.get("csrf_token")
    form_data = await request.form()
    request_csrf = form_data.get("csrf_token")
    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(request_csrf)):
        return RedirectResponse(url="/admin/keepers?msg=csrf_error", status_code=303)
        
    try:
        execute_query("INSERT INTO users (username, password, role) VALUES (%s, %s, 'keeper')", (username, password))
        
        user_row = execute_query("SELECT user_id FROM users WHERE username = %s", (username,))
        new_user_id = user_row[0]['user_id']
        
        execute_query(
            "INSERT INTO keepers (user_id, name, shift, phone_number) VALUES (%s, %s, %s, %s)",
            (new_user_id, name, shift, phone_number)
        )
    except Exception as e:
        return RedirectResponse(url=f"/admin/keepers?msg=error", status_code=303)
        
    return RedirectResponse(url="/admin/keepers", status_code=303)

@router.post("/delete/{keeper_id}")
async def delete_keeper(request: Request, keeper_id: int):
    rows = execute_query("SELECT user_id FROM keepers WHERE keeper_id = %s", (keeper_id,))
    if rows:
        user_id = rows[0]['user_id']
        execute_query("DELETE FROM keepers WHERE keeper_id = %s", (keeper_id,))
        execute_query("DELETE FROM users WHERE user_id = %s", (user_id,))
        
    return RedirectResponse(url="/admin/keepers", status_code=303)

@router.post("/edit/{keeper_id}")
async def edit_keeper(
    request: Request,
    keeper_id: int,
    username: str = Form(...),
    name: str = Form(...),
    shift: str = Form(...),
    phone_number: str = Form(...)
):
    session_csrf = request.session.get("csrf_token")
    form_data = await request.form()
    request_csrf = form_data.get("csrf_token")
    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(request_csrf)):
        return RedirectResponse(url="/admin/keepers?msg=csrf_error", status_code=303)

    
    try:
        execute_query(
            "UPDATE keepers SET name = %s, shift = %s, phone_number = %s WHERE keeper_id = %s",
            (name, shift, phone_number, keeper_id)
        )
        
        k_rows = execute_query("SELECT user_id FROM keepers WHERE keeper_id = %s", (keeper_id,))
        if k_rows:
            execute_query(
                "UPDATE users SET username = %s WHERE user_id = %s",
                (username, k_rows[0]['user_id'])
            )
            
    except Exception as e:
        if "Duplicate entry" in str(e):
            return RedirectResponse(url="/admin/keepers?msg=duplicate_error", status_code=303)
        return RedirectResponse(url="/admin/keepers?msg=error", status_code=303)
        
    return RedirectResponse(url="/admin/keepers", status_code=303)
