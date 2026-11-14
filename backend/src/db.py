import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.config import DB_PATH

def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Optional[Path] = None) -> None:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        case_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        persona_id TEXT NOT NULL,
        status TEXT NOT NULL,
        moment TEXT NOT NULL,
        language TEXT NOT NULL,
        facts_json TEXT NOT NULL,
        playbook_id TEXT NOT NULL,
        proposed_action TEXT,
        action_label TEXT,
        action_params_json TEXT,
        allowed_actions_json TEXT,
        cause_explanation TEXT,
        visual_data_json TEXT,
        source_mode TEXT DEFAULT 'template',
        receipt_json TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        entry_id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        stage TEXT NOT NULL,
        layer TEXT NOT NULL,
        is_ai INTEGER NOT NULL,
        idempotency_key TEXT,
        details_json TEXT NOT NULL,
        FOREIGN KEY (case_id) REFERENCES cases(case_id)
    )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_case ON audit_log(case_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_idempotency ON audit_log(idempotency_key)")
    
    conn.commit()
    conn.close()

def save_case(case_data: Dict[str, Any], db_path: Optional[Path] = None) -> None:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("""
    INSERT INTO cases (
        case_id, customer_id, persona_id, status, moment, language,
        facts_json, playbook_id, proposed_action, action_label,
        action_params_json, allowed_actions_json, cause_explanation,
        visual_data_json, source_mode, receipt_json, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(case_id) DO UPDATE SET
        status = excluded.status,
        language = excluded.language,
        proposed_action = excluded.proposed_action,
        action_label = excluded.action_label,
        action_params_json = excluded.action_params_json,
        allowed_actions_json = excluded.allowed_actions_json,
        cause_explanation = excluded.cause_explanation,
        visual_data_json = excluded.visual_data_json,
        source_mode = excluded.source_mode,
        receipt_json = excluded.receipt_json,
        updated_at = excluded.updated_at
    """, (
        case_data["case_id"],
        case_data["customer_id"],
        case_data["persona_id"],
        case_data["status"],
        case_data["moment"],
        case_data["language"],
        json.dumps(case_data.get("facts", {})),
        case_data["playbook_id"],
        case_data.get("proposed_action"),
        case_data.get("action_label"),
        json.dumps(case_data.get("action_params", {})),
        json.dumps(case_data.get("allowed_actions", [])),
        case_data.get("cause_explanation"),
        json.dumps(case_data.get("visual_data", {})),
        case_data.get("source_mode", "template"),
        json.dumps(case_data.get("receipt")) if case_data.get("receipt") else None,
        case_data.get("created_at", now_iso),
        now_iso
    ))
    
    conn.commit()
    conn.close()

def get_case(case_id: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    return {
        "case_id": row["case_id"],
        "customer_id": row["customer_id"],
        "persona_id": row["persona_id"],
        "status": row["status"],
        "moment": row["moment"],
        "language": row["language"],
        "facts": json.loads(row["facts_json"]),
        "playbook_id": row["playbook_id"],
        "proposed_action": row["proposed_action"],
        "action_label": row["action_label"],
        "action_params": json.loads(row["action_params_json"]) if row["action_params_json"] else {},
        "allowed_actions": json.loads(row["allowed_actions_json"]) if row["allowed_actions_json"] else [],
        "cause_explanation": row["cause_explanation"],
        "visual_data": json.loads(row["visual_data_json"]) if row["visual_data_json"] else {},
        "source_mode": row["source_mode"],
        "receipt": json.loads(row["receipt_json"]) if row["receipt_json"] else None,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }

def add_audit_entry(
    case_id: str,
    stage: str,
    layer: str,
    is_ai: bool,
    details: Dict[str, Any],
    idempotency_key: Optional[str] = None,
    db_path: Optional[Path] = None
) -> Dict[str, Any]:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    entry_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("""
    INSERT INTO audit_log (
        entry_id, case_id, timestamp, stage, layer, is_ai, idempotency_key, details_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        entry_id,
        case_id,
        now_iso,
        stage,
        layer,
        1 if is_ai else 0,
        idempotency_key,
        json.dumps(details)
    ))
    
    conn.commit()
    conn.close()
    
    return {
        "entry_id": entry_id,
        "case_id": case_id,
        "timestamp": now_iso,
        "stage": stage,
        "layer": layer,
        "is_ai": is_ai,
        "idempotency_key": idempotency_key,
        "details": details
    }

def get_audit_trail(case_id: str, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_log WHERE case_id = ? ORDER BY rowid ASC", (case_id,))
    rows = cursor.fetchall()
    conn.close()
    
    trail = []
    for r in rows:
        trail.append({
            "entry_id": r["entry_id"],
            "case_id": r["case_id"],
            "timestamp": r["timestamp"],
            "stage": r["stage"],
            "layer": r["layer"],
            "is_ai": bool(r["is_ai"]),
            "idempotency_key": r["idempotency_key"],
            "details": json.loads(r["details_json"])
        })
    return trail

def check_idempotency(case_id: str, idempotency_key: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    if not idempotency_key:
        return None
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT details_json FROM audit_log 
    WHERE case_id = ? AND idempotency_key = ? AND stage = 'ACTION'
    ORDER BY rowid DESC LIMIT 1
    """, (case_id, idempotency_key))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row["details_json"])
    return None

def reset_db(db_path: Optional[Path] = None) -> None:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM audit_log")
    cursor.execute("DELETE FROM cases")
    conn.commit()
    conn.close()

