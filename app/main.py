from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import os
import secrets
from .database import execute_query

app = FastAPI(title="PokeZOO API")

def get_secret():
    if os.getenv('JWT_SECRET_KEY'):
        return os.getenv('JWT_SECRET_KEY')
    
    import logging
    logging.warning("Generating ephemeral secret. Instance-isolated!")
    return secrets.token_hex(32)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.add_middleware(
    SessionMiddleware, 
    secret_key=get_secret(), 
    session_cookie="session", 
    max_age=3600, 
    same_site="lax", 
    https_only=False 
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; frame-ancestors 'self';"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    role = request.session.get("role")
    if not user_id or not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return {"user_id": user_id, "role": role}

def require_role(allowed_roles: list):
    def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        return user
    return role_checker

@app.get("/pokemon.png", include_in_schema=False)
async def pokemon_png():
    return FileResponse("app/static/pokemon.png")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get("user_id")
    if user:
        role = request.session.get("role")
        return RedirectResponse(url=f"/{role}/dashboard", status_code=303)
    return RedirectResponse(url="/auth/login", status_code=303)

from .routes import auth, admin, keeper, visitor
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(keeper.router, prefix="/keeper", tags=["keeper"])
app.include_router(visitor.router, prefix="/visitor", tags=["visitor"])
