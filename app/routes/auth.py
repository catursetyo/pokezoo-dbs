from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ..database import execute_query, get_mysql_connection
import secrets

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)

    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "csrf_token": request.session["csrf_token"]
    })
    
@router.post("/login")
async def login(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...),
    csrf_token: str = Form(...)
):
    session_csrf = request.session.get("csrf_token")
    
    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(csrf_token)):
        request.session["csrf_token"] = secrets.token_urlsafe(32)

        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": "Invalid CSRF token. Please refresh and try again.",
            "csrf_token": request.session["csrf_token"]
        })
        
    users = execute_query("SELECT user_id, password, role FROM users WHERE username = %s", (username,))
    
    if not users:
        return templates.TemplateResponse("auth/login.html", {"request": request, "error": "Invalid username or password", "csrf_token": request.session.get("csrf_token")})
        
    user = users[0]
    
    if password != user['password']:
        return templates.TemplateResponse("auth/login.html", {"request": request, "error": "Invalid username or password", "csrf_token": request.session.get("csrf_token")})
    
    request.session.clear()
    request.session["user_id"] = user["user_id"]
    request.session["role"] = user["role"]
    request.session["csrf_token"] = secrets.token_urlsafe(32) # New CSRF token for the logged in session
    
    return RedirectResponse(url=f"/{user['role']}/dashboard", status_code=303)

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)

    return templates.TemplateResponse("auth/register.html", {
        "request": request,
        "csrf_token": request.session["csrf_token"]
    })


@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    name: str = Form(...),
    email: str = Form(""),
    phone_number: str = Form(""),
    csrf_token: str = Form(...)
):
    session_csrf = request.session.get("csrf_token")

    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(csrf_token)):
            request.session["csrf_token"] = secrets.token_urlsafe(32)
        
            return templates.TemplateResponse("auth/register.html", {
                "request": request,
                "error": "Invalid CSRF token. Please refresh and try again.",
                "csrf_token": request.session["csrf_token"]
            })

    username = username.strip()
    name = name.strip()
    email = email.strip()
    phone_number = phone_number.strip()

    if not username or not password or not confirm_password or not name:
        return templates.TemplateResponse("auth/register.html", {
            "request": request,
            "error": "Username, password, confirmation password, and name are required.",
            "csrf_token": session_csrf,
            "form": {
                "username": username,
                "name": name,
                "email": email,
                "phone_number": phone_number
            }
        })

    if password != confirm_password:
        return templates.TemplateResponse("auth/register.html", {
            "request": request,
            "error": "Password confirmation does not match.",
            "csrf_token": session_csrf,
            "form": {
                "username": username,
                "name": name,
                "email": email,
                "phone_number": phone_number
            }
        })

    existing_user = execute_query(
        "SELECT user_id FROM users WHERE username = %s",
        (username,)
    )

    if existing_user:
        return templates.TemplateResponse("auth/register.html", {
            "request": request,
            "error": "Username already exists. Please choose another username.",
            "csrf_token": session_csrf,
            "form": {
                "username": username,
                "name": name,
                "email": email,
                "phone_number": phone_number
            }
        })

    connection = get_mysql_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (username, password, role)
                VALUES (%s, %s, 'visitor')
                """,
                (username, password)
            )

            new_user_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO visitors (user_id, name, email, phone_number)
                VALUES (%s, %s, %s, %s)
                """,
                (new_user_id, name, email if email else None, phone_number if phone_number else None)
            )

        connection.commit()

    except Exception:
        connection.rollback()

        return templates.TemplateResponse("auth/register.html", {
            "request": request,
            "error": "Registration failed. Please try again.",
            "csrf_token": session_csrf,
            "form": {
                "username": username,
                "name": name,
                "email": email,
                "phone_number": phone_number
            }
        })

    finally:
        connection.close()

    return RedirectResponse(url="/auth/login?msg=registered", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear() # MUST invalidate all sessions
    return RedirectResponse(url="/auth/login", status_code=303)
