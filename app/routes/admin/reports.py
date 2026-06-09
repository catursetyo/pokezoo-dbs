from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ...database import execute_query, get_mongo_db
from ...main import require_role

router = APIRouter(dependencies=[Depends(require_role(["admin"]))])
templates = Jinja2Templates(directory="app/templates")


def get_visitor_map(visitor_ids):
    clean_ids = []

    for visitor_id in visitor_ids:
        if visitor_id is None:
            continue
        try:
            clean_ids.append(int(visitor_id))
        except (ValueError, TypeError):
            continue

    clean_ids = list(set(clean_ids))

    if not clean_ids:
        return {}

    placeholders = ", ".join(["%s"] * len(clean_ids))

    rows = execute_query(f"""
        SELECT visitor_id, name, email
        FROM visitors
        WHERE visitor_id IN ({placeholders})
    """, tuple(clean_ids))

    return {row["visitor_id"]: row for row in rows}


def get_habitat_map(habitat_ids):
    clean_ids = []

    for habitat_id in habitat_ids:
        if habitat_id is None:
            continue
        try:
            clean_ids.append(int(habitat_id))
        except (ValueError, TypeError):
            continue

    clean_ids = list(set(clean_ids))

    if not clean_ids:
        return {}

    placeholders = ", ".join(["%s"] * len(clean_ids))

    rows = execute_query(f"""
        SELECT habitat_id, habitat_name
        FROM habitats
        WHERE habitat_id IN ({placeholders})
    """, tuple(clean_ids))

    return {row["habitat_id"]: row for row in rows}


def get_pokemon_map(pokemon_ids):
    clean_ids = []

    for pokemon_id in pokemon_ids:
        if pokemon_id is None:
            continue
        try:
            clean_ids.append(int(pokemon_id))
        except (ValueError, TypeError):
            continue

    clean_ids = list(set(clean_ids))

    if not clean_ids:
        return {}

    placeholders = ", ".join(["%s"] * len(clean_ids))

    rows = execute_query(f"""
        SELECT
            p.pokemon_id,
            p.nickname,
            ps.species_name
        FROM pokemon p
        JOIN pokemon_species ps ON p.species_id = ps.species_id
        WHERE p.pokemon_id IN ({placeholders})
    """, tuple(clean_ids))

    return {row["pokemon_id"]: row for row in rows}


@router.get("/reports", response_class=HTMLResponse)
async def reports(request: Request):
    db = await get_mongo_db()

    reviews_col = db["visitor_reviews"]
    incidents_col = db["incident_reports"]
    behavior_col = db["pokemon_behavior_logs"]

    # ==========================
    # Visitor Reviews Summary
    # ==========================
    review_summary = await reviews_col.aggregate([
        {
            "$group": {
                "_id": None,
                "total_reviews": {"$sum": 1},
                "avg_rating": {"$avg": "$rating"},
                "min_rating": {"$min": "$rating"},
                "max_rating": {"$max": "$rating"}
            }
        }
    ]).to_list(length=1)

    review_stats = review_summary[0] if review_summary else {
        "total_reviews": 0,
        "avg_rating": 0,
        "min_rating": 0,
        "max_rating": 0
    }

    if review_stats.get("avg_rating") is None:
        review_stats["avg_rating"] = 0

    review_stats["avg_rating"] = round(float(review_stats["avg_rating"]), 2)

    rating_distribution = await reviews_col.aggregate([
        {
            "$group": {
                "_id": "$rating",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": -1}}
    ]).to_list(length=10)

    review_history = await reviews_col.find({}).sort(
        "date_submitted", -1
    ).to_list(length=20)

    review_visitor_ids = [
        review.get("visitor_id")
        for review in review_history
        if review.get("visitor_id") is not None
    ]

    visitor_map = get_visitor_map(review_visitor_ids)

    for review in review_history:
        review["_id"] = str(review["_id"])
        review["comment_text"] = review.get("comment") or "No comment"

        try:
            visitor_id = int(review.get("visitor_id"))
        except (ValueError, TypeError):
            visitor_id = None

        visitor = visitor_map.get(visitor_id)

        if visitor:
            review["visitor_name"] = visitor["name"]
            review["visitor_email"] = visitor.get("email")
        else:
            review["visitor_name"] = f"Visitor #{review.get('visitor_id')}"
            review["visitor_email"] = None

    # ==========================
    # Incident Reports Summary
    # ==========================
    total_incidents = await incidents_col.count_documents({})

    incident_severity_distribution = await incidents_col.aggregate([
        {
            "$group": {
                "_id": "$severity",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}}
    ]).to_list(length=10)

    incident_per_habitat_raw = await incidents_col.aggregate([
        {
            "$group": {
                "_id": "$habitat_id",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}}
    ]).to_list(length=20)

    incident_habitat_ids = [
        item.get("_id")
        for item in incident_per_habitat_raw
        if item.get("_id") is not None
    ]

    habitat_map = get_habitat_map(incident_habitat_ids)

    incident_per_habitat = []

    for item in incident_per_habitat_raw:
        try:
            habitat_id = int(item.get("_id")) if item.get("_id") is not None else None
        except (ValueError, TypeError):
            habitat_id = None

        habitat = habitat_map.get(habitat_id)

        incident_per_habitat.append({
            "habitat_id": habitat_id,
            "habitat_name": habitat["habitat_name"] if habitat else "Unknown Habitat",
            "count": item["count"]
        })

    incident_history = await incidents_col.find({}).sort(
        "date_reported", -1
    ).to_list(length=20)

    incident_pokemon_ids = [
        incident.get("pokemon_id")
        for incident in incident_history
        if incident.get("pokemon_id") is not None
    ]

    incident_history_habitat_ids = [
        incident.get("habitat_id")
        for incident in incident_history
        if incident.get("habitat_id") is not None
    ]

    pokemon_map = get_pokemon_map(incident_pokemon_ids)
    incident_habitat_map = get_habitat_map(incident_history_habitat_ids)

    for incident in incident_history:
        incident["_id"] = str(incident["_id"])

        try:
            pokemon_id = int(incident.get("pokemon_id")) if incident.get("pokemon_id") is not None else None
        except (ValueError, TypeError):
            pokemon_id = None

        try:
            habitat_id = int(incident.get("habitat_id")) if incident.get("habitat_id") is not None else None
        except (ValueError, TypeError):
            habitat_id = None

        pokemon = pokemon_map.get(pokemon_id)
        habitat = incident_habitat_map.get(habitat_id)

        incident["pokemon_name"] = (
            pokemon["nickname"] or pokemon["species_name"]
            if pokemon else "No specific Pokémon"
        )
        incident["habitat_name"] = habitat["habitat_name"] if habitat else "Unknown Habitat"

        if isinstance(incident.get("actions_taken"), list):
            incident["actions_taken_text"] = ", ".join(incident["actions_taken"])
        else:
            incident["actions_taken_text"] = incident.get("actions_taken", "")

    # ==========================
    # Behavior Reports Summary
    # ==========================
    total_behavior_reports = await behavior_col.count_documents({})

    behavior_mood_distribution = await behavior_col.aggregate([
        {
            "$group": {
                "_id": "$mood",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}}
    ]).to_list(length=10)

    behavior_per_pokemon_raw = await behavior_col.aggregate([
        {
            "$group": {
                "_id": "$pokemon_id",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}}
    ]).to_list(length=20)

    behavior_pokemon_ids = [
        item.get("_id")
        for item in behavior_per_pokemon_raw
        if item.get("_id") is not None
    ]

    behavior_pokemon_map = get_pokemon_map(behavior_pokemon_ids)

    behavior_per_pokemon = []

    for item in behavior_per_pokemon_raw:
        try:
            pokemon_id = int(item.get("_id")) if item.get("_id") is not None else None
        except (ValueError, TypeError):
            pokemon_id = None

        pokemon = behavior_pokemon_map.get(pokemon_id)

        behavior_per_pokemon.append({
            "pokemon_id": pokemon_id,
            "pokemon_name": (
                pokemon["nickname"] or pokemon["species_name"]
                if pokemon else f"Pokémon #{item.get('_id')}"
            ),
            "count": item["count"]
        })

    behavior_history = await behavior_col.find({}).sort([
        ("date", -1),
        ("time", -1)
    ]).to_list(length=20)

    behavior_history_pokemon_ids = [
        log.get("pokemon_id")
        for log in behavior_history
        if log.get("pokemon_id") is not None
    ]

    behavior_history_pokemon_map = get_pokemon_map(behavior_history_pokemon_ids)

    for log in behavior_history:
        log["_id"] = str(log["_id"])

        try:
            pokemon_id = int(log.get("pokemon_id")) if log.get("pokemon_id") is not None else None
        except (ValueError, TypeError):
            pokemon_id = None

        pokemon = behavior_history_pokemon_map.get(pokemon_id)

        log["pokemon_name"] = (
            pokemon["nickname"] or pokemon["species_name"]
            if pokemon else f"Pokémon #{log.get('pokemon_id')}"
        )

    return templates.TemplateResponse("admin/reports.html", {
        "request": request,
        "review_stats": review_stats,
        "rating_distribution": rating_distribution,
        "review_history": review_history,
        "total_incidents": total_incidents,
        "incident_severity_distribution": incident_severity_distribution,
        "incident_per_habitat": incident_per_habitat,
        "incident_history": incident_history,
        "total_behavior_reports": total_behavior_reports,
        "behavior_mood_distribution": behavior_mood_distribution,
        "behavior_per_pokemon": behavior_per_pokemon,
        "behavior_history": behavior_history
    })
