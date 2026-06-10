from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ...database import get_mongo_db
from ...main import require_role
import secrets
import json

router = APIRouter(dependencies=[Depends(require_role(["admin"]))])
templates = Jinja2Templates(directory="app/templates")

ALLOWED_COLLECTIONS = {
    "behavior_logs": "pokemon_behavior_logs",
    "incident_reports": "incident_reports",
    "visitor_reviews": "visitor_reviews"
}

@router.get("/mongo-playground", response_class=HTMLResponse)
async def mongo_playground_page(request: Request):
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
        
    return templates.TemplateResponse("admin/mongo_playground.html", {
        "request": request, 
        "csrf_token": request.session["csrf_token"],
        "collections": ALLOWED_COLLECTIONS.keys(),
        "query": "{\n  \n}"
    })

@router.post("/mongo-playground", response_class=HTMLResponse)
async def execute_mongo_playground(
    request: Request, 
    collection: str = Form(...),
    query: str = Form(...)
):
    if collection not in ALLOWED_COLLECTIONS:
        return templates.TemplateResponse("admin/mongo_playground.html", {
            "request": request,
            "error": "Invalid collection selected.",
            "query": query,
            "selected_collection": collection,
            "collections": ALLOWED_COLLECTIONS.keys(),
            "csrf_token": request.session.get("csrf_token")
        })

    try:
        # Parse JSON query
        query_dict = json.loads(query) if query.strip() else {}
    except json.JSONDecodeError as e:
        return templates.TemplateResponse("admin/mongo_playground.html", {
            "request": request,
            "error": f"Invalid JSON format: {str(e)}",
            "query": query,
            "selected_collection": collection,
            "collections": ALLOWED_COLLECTIONS.keys(),
            "csrf_token": request.session.get("csrf_token")
        })

    db = await get_mongo_db()
    coll = db[ALLOWED_COLLECTIONS[collection]]
    documents = []
    
    try:
        # Execute query (limit to 100 for safety)
        cursor = coll.find(query_dict).limit(100)
        async for document in cursor:
            document["_id"] = str(document["_id"])
            documents.append(document)
            
        return templates.TemplateResponse("admin/mongo_playground.html", {
            "request": request, 
            "results": json.dumps(documents, indent=2),
            "result_count": len(documents),
            "query": query,
            "selected_collection": collection,
            "collections": ALLOWED_COLLECTIONS.keys(),
            "csrf_token": request.session.get("csrf_token")
        })
    except Exception as e:
        return templates.TemplateResponse("admin/mongo_playground.html", {
            "request": request, 
            "error": f"Database Execution Error: {str(e)}",
            "query": query,
            "selected_collection": collection,
            "collections": ALLOWED_COLLECTIONS.keys(),
            "csrf_token": request.session.get("csrf_token")
        })
