from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ...main import require_role
from ...database import execute_query
import secrets

router = APIRouter(dependencies=[Depends(require_role(["admin"]))])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_types(request: Request):
    types_list = execute_query("SELECT type_id, type_name FROM pokemon_types ORDER BY type_name")
    
    edit_id = request.query_params.get("edit_id")
    edit_item = None
    if edit_id:
        rows = execute_query("SELECT * FROM pokemon_types WHERE type_id = %s", (edit_id,))
        if rows:
            edit_item = rows[0]

    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
        
    return templates.TemplateResponse("admin/types.html", {
        "request": request, 
        "types_list": types_list,
        "edit_item": edit_item,
        "csrf_token": request.session["csrf_token"]
    })

@router.post("/add")
async def add_type(
    request: Request,
    type_name: str = Form(...)
):
    session_csrf = request.session.get("csrf_token")
    form_data = await request.form()
    request_csrf = form_data.get("csrf_token")
    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(request_csrf)):
        return RedirectResponse(url="/admin/types?msg=csrf_error", status_code=303)
        
    existing = execute_query(
        "SELECT type_id FROM pokemon_types WHERE LOWER(type_name) = LOWER(%s)",
        (type_name,)
    )
    if existing:
        return RedirectResponse(url="/admin/types?msg=duplicate_error", status_code=303)

    try:
        execute_query(
            "INSERT INTO pokemon_types (type_name) VALUES (%s)",
            (type_name,)
        )
    except Exception as e:
        if "Duplicate entry" in str(e):
            return RedirectResponse(url="/admin/types?msg=duplicate_error", status_code=303)
        return RedirectResponse(url="/admin/types?msg=error", status_code=303)
        
    return RedirectResponse(url="/admin/types", status_code=303)

@router.post("/edit/{type_id}")
async def edit_type(
    request: Request,
    type_id: int,
    type_name: str = Form(...)
):
    session_csrf = request.session.get("csrf_token")
    form_data = await request.form()
    request_csrf = form_data.get("csrf_token")
    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(request_csrf)):
        return RedirectResponse(url="/admin/types?msg=csrf_error", status_code=303)

    existing = execute_query(
        "SELECT type_id FROM pokemon_types WHERE LOWER(type_name) = LOWER(%s) AND type_id != %s",
        (type_name, type_id)
    )
    if existing:
        return RedirectResponse(url="/admin/types?msg=duplicate_error", status_code=303)

    try:
        execute_query(
            "UPDATE pokemon_types SET type_name = %s WHERE type_id = %s",
            (type_name, type_id)
        )
    except Exception as e:
        if "Duplicate entry" in str(e):
            return RedirectResponse(url="/admin/types?msg=duplicate_error", status_code=303)
        return RedirectResponse(url="/admin/types?msg=error", status_code=303)
        
    return RedirectResponse(url="/admin/types", status_code=303)

@router.post("/delete/{type_id}")
async def delete_type(request: Request, type_id: int):
    try:
        execute_query("DELETE FROM pokemon_types WHERE type_id = %s", (type_id,))
    except Exception as e:
        return RedirectResponse(url="/admin/types?msg=in_use_error", status_code=303)
    
    return RedirectResponse(url="/admin/types", status_code=303)
