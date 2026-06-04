from ...main import require_role
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ...database import execute_query
import secrets

router = APIRouter(dependencies=[Depends(require_role(["admin"]))])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_schedules(request: Request):
    schedules = execute_query("""
        SELECT fs.feeding_id, p.nickname, k.name as keeper_name, f.food_name, fs.feeding_time, fs.status
        FROM feeding_schedules fs
        JOIN pokemon p ON fs.pokemon_id = p.pokemon_id
        JOIN keepers k ON fs.keeper_id = k.keeper_id
        JOIN foods f ON fs.food_id = f.food_id
        ORDER BY fs.feeding_time DESC
    """)
    
    pokemon_list = execute_query("SELECT pokemon_id, nickname FROM pokemon ORDER BY nickname")
    keepers_list = execute_query("SELECT keeper_id, name FROM keepers ORDER BY name")
    foods_list = execute_query("""
        SELECT food_id, food_name, stock
        FROM foods
        ORDER BY food_name
    """)
    
    edit_id = request.query_params.get("edit_id")
    edit_item = None
    if edit_id:
        rows = execute_query("SELECT * FROM feeding_schedules WHERE feeding_id = %s", (edit_id,))
        if rows:
            edit_item = rows[0]
            if edit_item['feeding_time']:
                edit_item['html_time'] = edit_item['feeding_time'].strftime('%Y-%m-%dT%H:%M')

    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
        
    return templates.TemplateResponse("admin/schedules.html", {
        "request": request, 
        "schedules": schedules,
        "pokemon_list": pokemon_list,
        "keepers_list": keepers_list,
        "foods_list": foods_list,
        "edit_item": edit_item,
        "csrf_token": request.session["csrf_token"]
    })

@router.post("/add")
async def add_schedule(
    request: Request,
    pokemon_id: int = Form(...),
    keeper_id: int = Form(...),
    food_id: int = Form(...),
    feeding_time: str = Form(...)
):
    session_csrf = request.session.get("csrf_token")
    form_data = await request.form()
    request_csrf = form_data.get("csrf_token")

    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(request_csrf)):
        return RedirectResponse(url="/admin/schedules?msg=csrf_error", status_code=303)

    try:
        food_rows = execute_query(
            "SELECT stock FROM foods WHERE food_id = %s",
            (food_id,)
        )

        if not food_rows or food_rows[0]["stock"] <= 0:
            return RedirectResponse(url="/admin/schedules?msg=stock_error", status_code=303)

        mysql_time = feeding_time.replace("T", " ") + ":00"

        execute_query(
            """
            INSERT INTO feeding_schedules 
            (pokemon_id, keeper_id, food_id, feeding_time)
            VALUES (%s, %s, %s, %s)
            """,
            (pokemon_id, keeper_id, food_id, mysql_time)
        )

    except Exception:
        return RedirectResponse(url="/admin/schedules?msg=error", status_code=303)

    return RedirectResponse(url="/admin/schedules", status_code=303)

@router.post("/edit/{feeding_id}")
async def edit_schedule(
    request: Request,
    feeding_id: int,
    pokemon_id: int = Form(...),
    keeper_id: int = Form(...),
    food_id: int = Form(...),
    feeding_time: str = Form(...),
    status: str = Form("scheduled")
):
    session_csrf = request.session.get("csrf_token")
    form_data = await request.form()
    request_csrf = form_data.get("csrf_token")

    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(request_csrf)):
        return RedirectResponse(url="/admin/schedules?msg=csrf_error", status_code=303)

    try:
        food_rows = execute_query(
            "SELECT stock FROM foods WHERE food_id = %s",
            (food_id,)
        )

        if not food_rows or food_rows[0]["stock"] <= 0:
            return RedirectResponse(url="/admin/schedules?msg=stock_error", status_code=303)

        mysql_time = feeding_time.replace("T", " ")
        if len(mysql_time) == 16:
            mysql_time += ":00"

        execute_query(
            """
            UPDATE feeding_schedules
            SET pokemon_id = %s,
                keeper_id = %s,
                food_id = %s,
                feeding_time = %s,
                status = %s
            WHERE feeding_id = %s
            """,
            (pokemon_id, keeper_id, food_id, mysql_time, status, feeding_id)
        )

    except Exception:
        return RedirectResponse(url="/admin/schedules?msg=error", status_code=303)

    return RedirectResponse(url="/admin/schedules", status_code=303)
