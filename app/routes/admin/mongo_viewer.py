from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ...database import get_mongo_db
from ...main import require_role
import json

router = APIRouter(dependencies=[Depends(require_role(["admin"]))])
templates = Jinja2Templates(directory="app/templates")

ALLOWED_COLLECTIONS = {
    "behavior_logs": "pokemon_behavior_logs",
    "incident_reports": "incident_reports",
    "visitor_reviews": "visitor_reviews"
}


@router.get("/mongo-viewer", response_class=HTMLResponse)
async def mongo_viewer(request: Request, collection: str = "behavior_logs"):
    db = await get_mongo_db()
    documents = []

    if collection not in ALLOWED_COLLECTIONS:
        collection = "behavior_logs"

    coll = db[ALLOWED_COLLECTIONS[collection]]
    cursor = coll.find({}).sort("_id", -1).limit(50)

    async for document in cursor:
        document["_id"] = str(document["_id"])
        documents.append(document)

    return templates.TemplateResponse("admin/mongo_viewer.html", {
        "request": request,
        "documents": documents,
        "current_collection": collection,
        "collections": ALLOWED_COLLECTIONS.keys(),
        "filter_query": "{}",
        "error": None
    })


@router.post("/mongo-viewer", response_class=HTMLResponse)
async def mongo_playground(
    request: Request,
    collection: str = Form(...),
    filter_query: str = Form("{}"),
    limit: int = Form(50)
):
    db = await get_mongo_db()
    documents = []
    error = None

    if collection not in ALLOWED_COLLECTIONS:
        collection = "behavior_logs"

    if limit < 1:
        limit = 1
    elif limit > 100:
        limit = 100

    try:
        query = json.loads(filter_query) if filter_query.strip() else {}

        if not isinstance(query, dict):
            raise ValueError("Filter must be a JSON object.")

        coll = db[ALLOWED_COLLECTIONS[collection]]
        cursor = coll.find(query).sort("_id", -1).limit(limit)

        async for document in cursor:
            document["_id"] = str(document["_id"])
            documents.append(document)

    except Exception as e:
        error = f"Invalid MongoDB filter: {str(e)}"

    return templates.TemplateResponse("admin/mongo_viewer.html", {
        "request": request,
        "documents": documents,
        "current_collection": collection,
        "collections": ALLOWED_COLLECTIONS.keys(),
        "filter_query": filter_query,
        "error": error
    })
