from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ...database import get_mongo_db
from ...main import require_role

router = APIRouter(dependencies=[Depends(require_role(["admin"]))])
templates = Jinja2Templates(directory="app/templates")

@router.get("/mongo-viewer", response_class=HTMLResponse)
async def mongo_viewer(request: Request, collection: str = "behavior_logs"):
    db = await get_mongo_db()
    documents = []
    
    allowed_collections = {
        "behavior_logs": "pokemon_behavior_logs",
        "incident_reports": "incident_reports",
        "visitor_reviews": "visitor_reviews"
    }
    
    if collection in allowed_collections:
        coll = db[allowed_collections[collection]]
        cursor = coll.find().limit(50) # Limit for demo
        async for document in cursor:
            document["_id"] = str(document["_id"])
            documents.append(document)
            
    return templates.TemplateResponse("admin/mongo_viewer.html", {
        "request": request, 
        "documents": documents,
        "current_collection": collection,
        "collections": allowed_collections.keys()
    })
