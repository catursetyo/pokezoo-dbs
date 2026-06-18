from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ...database import get_mysql_connection
from ...main import require_role
import pymysql
import secrets
import re

router = APIRouter(dependencies=[Depends(require_role(["admin"]))])
templates = Jinja2Templates(directory="app/templates")

def get_table_names():
    connection = get_mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            rows = cursor.fetchall()
            return [list(row.values())[0] for row in rows]
    finally:
        connection.close()

@router.get("/playground", response_class=HTMLResponse)
async def playground_page(request: Request):
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
    return templates.TemplateResponse("admin/playground.html", {
        "request": request, 
        "csrf_token": request.session["csrf_token"],
        "tables": get_table_names()
    })

@router.post("/playground", response_class=HTMLResponse)
async def execute_playground(request: Request, query: str = Form(...)):
    tables = get_table_names()
    forbidden_pattern = re.compile(r'\b(DROP\s+DATABASE|DROP\s+TABLE)\b', re.IGNORECASE)
    if forbidden_pattern.search(query):
        return templates.TemplateResponse("admin/playground.html", {
            "request": request, 
            "error": "Execution forbidden: DROP statements are not allowed.",
            "query": query,
            "csrf_token": request.session.get("csrf_token"),
            "tables": tables
        })

    connection = get_mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            
            columns = []
            if results and len(results) > 0:
                columns = list(results[0].keys())
                
            return templates.TemplateResponse("admin/playground.html", {
                "request": request, 
                "results": results,
                "columns": columns,
                "query": query,
                "csrf_token": request.session.get("csrf_token"),
                "tables": tables
            })
    except Exception as e:
        return templates.TemplateResponse("admin/playground.html", {
            "request": request, 
            "error": f"SQL Error: {str(e)}",
            "query": query,
            "csrf_token": request.session.get("csrf_token"),
            "tables": tables
        })
    finally:
        connection.close()
