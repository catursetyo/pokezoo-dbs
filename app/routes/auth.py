from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from ..database import execute_query
import secrets

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
    return templates.TemplateResponse("auth/login.html", {"request": request, "csrf_token": request.session["csrf_token"]})

@router.post("/login")
async def login(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...),
    csrf_token: str = Form(...)
):
    session_csrf = request.session.get("csrf_token")
    if not session_csrf or not secrets.compare_digest(str(session_csrf), str(csrf_token)):
        return templates.TemplateResponse("auth/login.html", {"request": request, "error": "Invalid CSRF token. Please refresh and try again.", "csrf_token": session_csrf})
    
    users = execute_query("SELECT user_id, password, role FROM users WHERE username = %s", (username,))
    
    if not users:
        return templates.TemplateResponse("auth/login.html", {"request": request, "error": "Invalid username or password", "csrf_token": request.session.get("csrf_token")})
        
    user = users[0]
    
    try:
        valid_password = pwd_context.verify(password, user['password'])
    except ValueError:
        valid_password = (password == user['password'])

    if not valid_password:
        return templates.TemplateResponse("auth/login.html", {"request": request, "error": "Invalid username or password", "csrf_token": request.session.get("csrf_token")})
    
    request.session.clear()
    request.session["user_id"] = user["user_id"]
    request.session["role"] = user["role"]
    request.session["csrf_token"] = secrets.token_urlsafe(32) # New CSRF token for the logged in session
    
    return RedirectResponse(url=f"/{user['role']}/dashboard", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear() # MUST invalidate all sessions
    return RedirectResponse(url="/auth/login", status_code=303)
