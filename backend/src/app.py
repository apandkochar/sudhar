import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from src.actions import ActionSecurityError, process_consent
from src.config import DATA_DIR, DEMO_MODE, DISCLAIMER, LENDER_NAME, PRODUCT_NAME
from src.db import get_audit_stats, get_audit_trail, get_case, init_db, list_recent_cases, reset_db
from src.orchestrator import load_playbooks, process_event
from src.schemas import CaseResponse, ConsentRequest, EventRequest

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database on startup
    init_db()
    yield

app = FastAPI(
    title=f"{PRODUCT_NAME} Backend API",
    description="Consent-first AI agent for Paytm loan journeys",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local Next.js frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "product": PRODUCT_NAME,
        "lender": LENDER_NAME,
        "demo_mode": DEMO_MODE,
        "disclaimer": DISCLAIMER
    }

@app.get("/api/personas")
def list_personas() -> List[Dict[str, Any]]:
    personas = []
    personas_dir = DATA_DIR / "personas"
    for p_file in personas_dir.glob("*.json"):
        with open(p_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            personas.append({
                "persona_id": data["persona_id"],
                "name": data["name"],
                "city": data.get("city"),
                "preferred_language": data["preferred_language"],
                "trigger_event": data["trigger_event"]
            })
    return personas

@app.post("/api/events", response_model=CaseResponse)
def handle_event(event_req: EventRequest) -> Dict[str, Any]:
    """
    Ingests failure events (MANDATE_FAILED, EMI_DEBITED_AFTER_CLOSURE, VKYC_DROPPED).
    Executes playbook -> rules -> template resolution -> consent proposal.
    """
    try:
        case_data = process_event(event_req)
        return case_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/api/cases", response_model=List[Dict[str, Any]])
def list_cases(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Returns recent cases for operator history and console selection.
    """
    return list_recent_cases(limit=limit)

@app.get("/api/cases/{case_id}", response_model=CaseResponse)
def fetch_case(case_id: str) -> Dict[str, Any]:
    """
    Fetches the full case state including the vertical audit trail for the operator console.
    """
    case = get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found"
        )
    case["audit_trail"] = get_audit_trail(case_id)
    return case

@app.get("/api/audit/stats")
def audit_stats() -> Dict[str, Any]:
    """
    Returns operator KPI metrics, audit trail counts, and SQLite persistence verification status.
    """
    return get_audit_stats()

@app.post("/api/consent")
def handle_consent(consent_req: ConsentRequest) -> Dict[str, Any]:
    """
    Executes the customer's consent decision.
    Strictly enforces allowlist, idempotency, and server-side customer ID injection.
    """
    try:
        result = process_consent(
            case_id=consent_req.case_id,
            action=consent_req.action,
            consent_given=consent_req.consent_given,
            selected_params=consent_req.selected_params or {},
            idempotency_key=consent_req.idempotency_key
        )
        return result
    except ActionSecurityError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/api/scenarios/reset")
def reset_scenario_data() -> Dict[str, str]:
    """
    Resets cases and audit tables to fresh state for repeatable live demonstrations.
    """
    reset_db()
    return {"status": "success", "message": "Demo database reset to clean state"}

