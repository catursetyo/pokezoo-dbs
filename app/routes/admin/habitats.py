from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ...database import execute_query
from ...main import require_role
import secrets

router = APIRouter(dependencies=[Depends(require_role(["admin"]))])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_habitats(request: Request):
    query = "SELECT habitat_id, habitat_name, habitat_type, capacity, status FROM habitats"
    habitats_list = execute_query(query)
    
    edit_id = request.query_params.get("edit_id")
    edit_item = None
    if edit_id:
        rows = execute_query("SELECT * FROM habitats WHERE habitat_id = %s", (edit_id,))
        if rows:
            edit_item = rows[0]
    
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
        
    return templates.TemplateResponse("admin/habitats.html", {
        "request": request, 
        "habitats_list": habitats_list,
        "edit_item": edit_item,
        "csrf_token": request.session["csrf_token"]
    })

@router.post("/add")
async def add_habitat(
    request: Request,
    habitat_name: str = Form(...),
    habitat_type: str = Form(...),
    capacity: int = Form(...)
):
    # Check CSRF
    session_csrf = request.session.get("csrf_token")
    form_data = await request.form()
    request_csrf = form_data.get("csrf_token")
    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(request_csrf)):
        return RedirectResponse(url="/admin/habitats?msg=csrf_error", status_code=303)

    # Check for duplicate habitat name
    existing = execute_query(
        "SELECT habitat_id FROM habitats WHERE LOWER(habitat_name) = LOWER(%s)",
        (habitat_name,)
    )
    if existing:
        return RedirectResponse(url="/admin/habitats?msg=duplicate_error", status_code=303)

    query = """
        INSERT INTO habitats (habitat_name, habitat_type, capacity)
        VALUES (%s, %s, %s)
    """
    try:
        execute_query(query, (habitat_name, habitat_type, capacity))
    except Exception as e:
        if "Duplicate entry" in str(e):
            return RedirectResponse(url="/admin/habitats?msg=duplicate_error", status_code=303)
        return RedirectResponse(url="/admin/habitats?msg=error", status_code=303)
        
    return RedirectResponse(url="/admin/habitats", status_code=303)

@router.post("/delete/{habitat_id}")
async def delete_habitat(request: Request, habitat_id: int):
    execute_query("DELETE FROM habitats WHERE habitat_id = %s", (habitat_id,))
    return RedirectResponse(url="/admin/habitats", status_code=303)

@router.post("/edit/{habitat_id}")
async def edit_habitat(
    request: Request,
    habitat_id: int,
    habitat_name: str = Form(...),
    habitat_type: str = Form(...),
    capacity: int = Form(...),
    status: str = Form(...)
):
    session_csrf = request.session.get("csrf_token")
    form_data = await request.form()
    request_csrf = form_data.get("csrf_token")
    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(request_csrf)):
        return RedirectResponse(url="/admin/habitats?msg=csrf_error", status_code=303)

    # Check for duplicate habitat name (excluding self)
    existing = execute_query(
        "SELECT habitat_id FROM habitats WHERE LOWER(habitat_name) = LOWER(%s) AND habitat_id != %s",
        (habitat_name, habitat_id)
    )
    if existing:
        return RedirectResponse(url="/admin/habitats?msg=duplicate_error", status_code=303)

    query = """
        UPDATE habitats 
        SET habitat_name = %s, habitat_type = %s, capacity = %s, status = %s
        WHERE habitat_id = %s
    """
    try:
        execute_query(query, (habitat_name, habitat_type, capacity, status, habitat_id))
    except Exception as e:
        if "Duplicate entry" in str(e):
            return RedirectResponse(url="/admin/habitats?msg=duplicate_error", status_code=303)
        return RedirectResponse(url="/admin/habitats?msg=error", status_code=303)
        
    return RedirectResponse(url="/admin/habitats", status_code=303)
