import os
import httpx
from typing import Dict, Any, Optional, List
from src.config import config
from src.db.mongo import get_mongo_client

async def check_component_health(component: str) -> Dict[str, Any]:
    """Consulta la salud del componente vía HTTP hacia Next.js con degradación controlada."""
    nextjs_health_url = config.NEXTJS_HEALTH_URL
    
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(2.5, connect=1.5)) as client:
            response = await client.get(nextjs_health_url)
            data = response.json()
            return {
                "component": component,
                "status": data.get("status", "UNKNOWN"),
                "latency_ms": data.get("latency_ms", 0),
                "is_operational": data.get("status") == "UP",
                "error_code": data.get("error_code")
            }
    except (httpx.TimeoutException, httpx.ConnectError):
        return {
            "component": component,
            "status": "UNKNOWN",
            "latency_ms": None,
            "is_operational": False,
            "error_code": "HEALTHCHECK_TIMEOUT"
        }
    except Exception as e:
        return {
            "component": component,
            "status": "UNKNOWN",
            "latency_ms": None,
            "is_operational": False,
            "error_code": str(e)
        }

async def query_historical_incidents(component: str, incident_type: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
    """Consulta incidentes pasados en MongoDB Atlas usando motor."""
    try:
        client = get_mongo_client()
        db = client.get_default_database("triage_db")
        
        query: Dict[str, Any] = {"component": component}
        if incident_type:
            query["incident_type"] = incident_type

        cursor = db.incident_history.find(query).sort("timestamp", -1).limit(limit)
        incidents: List[Dict[str, Any]] = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if "timestamp" in doc and hasattr(doc["timestamp"], "isoformat"):
                doc["timestamp"] = doc["timestamp"].isoformat()
            incidents.append(doc)

        if incidents:
            valid_mttr = [i["mttr_minutes"] for i in incidents if i.get("mttr_minutes")]
            valid_mttd = [i["mttd_minutes"] for i in incidents if i.get("mttd_minutes")]
            avg_mttr = sum(valid_mttr) / len(valid_mttr) if valid_mttr else None
            avg_mttd = sum(valid_mttd) / len(valid_mttd) if valid_mttd else None
        else:
            avg_mttr = None
            avg_mttd = None

        return {
            "component": component,
            "total_incidents": len(incidents),
            "incidents": incidents,
            "average_mttr_minutes": avg_mttr,
            "average_mttd_minutes": avg_mttd,
        }
    except Exception:
        # Fallback offline a fixtures locales si Mongo Atlas no está accesible
        from src.db.fixtures import HISTORICAL_INCIDENTS
        mock_matches = [i for i in HISTORICAL_INCIDENTS if i.get("component") == component]
        if not mock_matches:
            mock_matches = HISTORICAL_INCIDENTS[:2]
        
        valid_mttr = [i["mttr_minutes"] for i in mock_matches if i.get("mttr_minutes")]
        valid_mttd = [i["mttd_minutes"] for i in mock_matches if i.get("mttd_minutes")]
        avg_mttr = sum(valid_mttr) / len(valid_mttr) if valid_mttr else None
        avg_mttd = sum(valid_mttd) / len(valid_mttd) if valid_mttd else None

        return {
            "component": component,
            "total_incidents": len(mock_matches),
            "incidents": mock_matches,
            "average_mttr_minutes": avg_mttr,
            "average_mttd_minutes": avg_mttd,
        }

async def search_solutions_in_kb(incident_type: str, component: str) -> List[Dict[str, Any]]:
    """Busca soluciones en la base de conocimiento de MongoDB o fallback a KB local."""
    try:
        client = get_mongo_client()
        db = client.get_default_database("triage_db")
        cursor = db.knowledge_base.find({
            "$or": [
                {"incident_type": {"$regex": incident_type, "$options": "i"}},
                {"component": component}
            ]
        }).limit(3)
        
        solutions = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            solutions.append(doc)
        if solutions:
            return solutions
    except Exception:
        pass

    # Fallback a Knowledge Base local
    from src.db.fixtures import KB_DATA
    matching = [
        k for k in KB_DATA 
        if incident_type.lower() in k.get("incident_type", "").lower() 
        or component.lower() == k.get("component", "").lower()
    ]
    return matching if matching else KB_DATA[:1]

