from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ...database import get_mysql_connection
from ...main import require_role
import secrets
import re

router = APIRouter(dependencies=[Depends(require_role(["admin"]))])
templates = Jinja2Templates(directory="app/templates")

def get_table_schemas():
    connection = get_mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    TABLE_NAME AS table_name,
                    COLUMN_NAME AS column_name
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                ORDER BY TABLE_NAME, ORDINAL_POSITION
            """)
            rows = cursor.fetchall()

            tables = {}
            for row in rows:
                table_name = row["table_name"]
                tables.setdefault(table_name, []).append(row["column_name"])

            return [
                {"name": table_name, "columns": columns}
                for table_name, columns in tables.items()
            ]
    finally:
        connection.close()

@router.get("/playground", response_class=HTMLResponse)
async def playground_page(request: Request):
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
    return templates.TemplateResponse("admin/playground.html", {
        "request": request, 
        "csrf_token": request.session["csrf_token"],
        "table_schemas": get_table_schemas()
    })

@router.post("/playground", response_class=HTMLResponse)
async def execute_playground(request: Request, query: str = Form(...)):
    table_schemas = get_table_schemas()
    forbidden_pattern = re.compile(r'\b(DROP\s+DATABASE|DROP\s+TABLE)\b', re.IGNORECASE)
    if forbidden_pattern.search(query):
        return templates.TemplateResponse("admin/playground.html", {
            "request": request, 
            "error": "Execution forbidden: DROP statements are not allowed.",
            "query": query,
            "csrf_token": request.session.get("csrf_token"),
            "table_schemas": table_schemas
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
                "table_schemas": table_schemas
            })
    except Exception as e:
        return templates.TemplateResponse("admin/playground.html", {
            "request": request, 
            "error": f"SQL Error: {str(e)}",
            "query": query,
            "csrf_token": request.session.get("csrf_token"),
            "table_schemas": table_schemas
        })
    finally:
        connection.close()
