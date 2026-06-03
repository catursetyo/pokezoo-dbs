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

@router.get("/playground", response_class=HTMLResponse)
async def playground_page(request: Request):
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
    return templates.TemplateResponse("admin/playground.html", {
        "request": request, 
        "csrf_token": request.session["csrf_token"]
    })

@router.post("/playground", response_class=HTMLResponse)
async def execute_playground(request: Request, query: str = Form(...)):
    # Basic validation: block DROP statements
    # TODO(security): This is a very naive block for a demo. Real protection requires strict DB user permissions!
    # The prompt explicitly requires "Do NOT allow: DROP DATABASE, DROP TABLE"
    forbidden_pattern = re.compile(r'\b(DROP\s+DATABASE|DROP\s+TABLE)\b', re.IGNORECASE)
    if forbidden_pattern.search(query):
        return templates.TemplateResponse("admin/playground.html", {
            "request": request, 
            "error": "Execution forbidden: DROP statements are not allowed.",
            "query": query,
            "csrf_token": request.session.get("csrf_token")
        })

    connection = get_mysql_connection()
    try:
        with connection.cursor() as cursor:
            # We are explicitly allowing arbitrary SQL here as requested for the "SQL Playground" demo feature.
            # IN A REAL WORLD APP, THIS IS EXTREMELY DANGEROUS!
            cursor.execute(query)
            # If it's a select or call returning rows, fetch them
            results = cursor.fetchall()
            
            columns = []
            if results and len(results) > 0:
                columns = list(results[0].keys())
                
            return templates.TemplateResponse("admin/playground.html", {
                "request": request, 
                "results": results,
                "columns": columns,
                "query": query,
                "csrf_token": request.session.get("csrf_token")
            })
    except Exception as e:
        return templates.TemplateResponse("admin/playground.html", {
            "request": request, 
            "error": f"SQL Error: {str(e)}",
            "query": query,
            "csrf_token": request.session.get("csrf_token")
        })
    finally:
        connection.close()
