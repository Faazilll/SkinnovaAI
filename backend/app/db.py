"""
Database access and schema management for Skinova (SQLite).
Handles user accounts, authentication tokens, and scan history persistence.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DB_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "skinova.db"
SECRET_KEY = os.environ.get("SKINOVA_SECRET_KEY", "skinova-secret-key-2026-decision-support")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    created_at TEXT NOT NULL,
                    severity INTEGER NOT NULL,
                    severity_label TEXT NOT NULL,
                    risk_percent REAL NOT NULL,
                    skin_health_score REAL NOT NULL,
                    image_attributes TEXT NOT NULL,
                    data_scores TEXT NOT NULL,
                    drivers TEXT NOT NULL,
                    trend TEXT NOT NULL,
                    recommendations TEXT NOT NULL,
                    image_filename TEXT,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_scans_user ON scans(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_scans_created ON scans(created_at DESC)")
    finally:
        conn.close()


def _hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return key.hex(), salt


def _verify_password(password: str, password_hash: str, salt: str) -> bool:
    new_hash, _ = _hash_password(password, salt)
    return hmac.compare_digest(new_hash, password_hash)


def create_token(user_id: int, email: str) -> str:
    """Lightweight signed token with expiration timestamp."""
    payload = {
        "uid": user_id,
        "email": email,
        "exp": int(time.time()) + (30 * 86400),  # 30 days
        "nonce": secrets.token_hex(8),
    }
    raw = json.dumps(payload, separators=(",", ":"))
    sig = hmac.new(SECRET_KEY.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{raw.encode('utf-8').hex()}.{sig}"


def verify_token(token: str) -> Optional[dict[str, Any]]:
    if not token or "." not in token:
        return None
    try:
        raw_hex, sig = token.split(".", 1)
        raw = bytes.fromhex(raw_hex).decode("utf-8")
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload = json.loads(raw)
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


# User operations
def register_user(email: str, password: str, name: str) -> dict[str, Any]:
    email = email.strip().lower()
    name = name.strip() or email.split("@")[0].title()
    if len(password) < 4:
        raise ValueError("Password must be at least 4 characters long")
    if "@" not in email:
        raise ValueError("Invalid email address")

    p_hash, salt = _hash_password(password)
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO users (email, name, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?)",
                (email, name, p_hash, salt, now),
            )
            user_id = cur.lastrowid
        token = create_token(user_id, email)
        return {"id": user_id, "email": email, "name": name, "token": token, "created_at": now}
    except sqlite3.IntegrityError:
        raise ValueError("An account with this email already exists")
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> dict[str, Any]:
    email = email.strip().lower()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, email, name, password_hash, salt, created_at FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if not row:
            raise ValueError("Invalid email or password")
        if not _verify_password(password, row["password_hash"], row["salt"]):
            raise ValueError("Invalid email or password")
        token = create_token(row["id"], row["email"])
        return {
            "id": row["id"],
            "email": row["email"],
            "name": row["name"],
            "token": token,
            "created_at": row["created_at"],
        }
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[dict[str, Any]]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, email, name, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        return dict(row)
    finally:
        conn.close()


# Scan operations
def save_scan(scan_data: dict[str, Any], user_id: Optional[int] = None) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    severity = int(scan_data.get("image", {}).get("severity", 0))
    severity_label = scan_data.get("image", {}).get("severity_label", "Clear / Mild")
    risk_percent = float(scan_data.get("final_risk_percent", scan_data.get("image", {}).get("risk_percent", 0)))
    skin_health_score = float(scan_data.get("skin_health_score", 100.0 - risk_percent))
    
    img_attrs = json.dumps(
        {
            "oiliness": scan_data.get("image", {}).get("oiliness", 0),
            "pores": scan_data.get("image", {}).get("pores", 0),
            "redness": scan_data.get("image", {}).get("redness", 0),
            "dark_spots": scan_data.get("image", {}).get("dark_spots", 0),
            "current_skin_condition": scan_data.get("image", {}).get("current_skin_condition", severity_label),
            "problem_areas": scan_data.get("image", {}).get("problem_areas", []),
            "method": scan_data.get("image", {}).get("method", "improved_model"),
        }
    )
    data_scores = json.dumps(
        {
            "hormonal": scan_data.get("data", {}).get("hormonal_score", 0),
            "lifestyle": scan_data.get("data", {}).get("lifestyle_score", 0),
            "environmental": scan_data.get("data", {}).get("environmental_score", 0),
            "combined": scan_data.get("data", {}).get("combined_score", 0),
            "method": scan_data.get("data", {}).get("method", "rf"),
        }
    )
    drivers = json.dumps(scan_data.get("data", {}).get("drivers", []))
    trend = json.dumps(scan_data.get("trend", []))
    recommendations = json.dumps(scan_data.get("recommendations", {}))
    image_filename = scan_data.get("image_filename", "facial_scan.jpg")
    notes = scan_data.get("notes", "")

    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                """
                INSERT INTO scans (
                    user_id, created_at, severity, severity_label, risk_percent,
                    skin_health_score, image_attributes, data_scores, drivers,
                    trend, recommendations, image_filename, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    now,
                    severity,
                    severity_label,
                    risk_percent,
                    skin_health_score,
                    img_attrs,
                    data_scores,
                    drivers,
                    trend,
                    recommendations,
                    image_filename,
                    notes,
                ),
            )
            scan_id = cur.lastrowid
        return {"id": scan_id, "created_at": now, "user_id": user_id, "status": "saved"}
    finally:
        conn.close()


def list_scans(user_id: Optional[int] = None, limit: int = 50) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        if user_id is not None:
            rows = conn.execute(
                "SELECT * FROM scans WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM scans ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        
        result = []
        for r in rows:
            result.append(
                {
                    "id": r["id"],
                    "user_id": r["user_id"],
                    "created_at": r["created_at"],
                    "severity": r["severity"],
                    "severity_label": r["severity_label"],
                    "risk_percent": r["risk_percent"],
                    "skin_health_score": r["skin_health_score"],
                    "image_attributes": json.loads(r["image_attributes"]),
                    "data_scores": json.loads(r["data_scores"]),
                    "drivers": json.loads(r["drivers"]),
                    "trend": json.loads(r["trend"]),
                    "recommendations": json.loads(r["recommendations"]),
                    "image_filename": r["image_filename"],
                    "notes": r["notes"],
                }
            )
        return result
    finally:
        conn.close()


def get_scan(scan_id: int) -> Optional[dict[str, Any]]:
    conn = get_connection()
    try:
        r = conn.execute("SELECT * FROM scans WHERE id = ?", (scan_id,)).fetchone()
        if not r:
            return None
        return {
            "id": r["id"],
            "user_id": r["user_id"],
            "created_at": r["created_at"],
            "severity": r["severity"],
            "severity_label": r["severity_label"],
            "risk_percent": r["risk_percent"],
            "skin_health_score": r["skin_health_score"],
            "image_attributes": json.loads(r["image_attributes"]),
            "data_scores": json.loads(r["data_scores"]),
            "drivers": json.loads(r["drivers"]),
            "trend": json.loads(r["trend"]),
            "recommendations": json.loads(r["recommendations"]),
            "image_filename": r["image_filename"],
            "notes": r["notes"],
        }
    finally:
        conn.close()


def delete_scan(scan_id: int, user_id: Optional[int] = None) -> bool:
    conn = get_connection()
    try:
        with conn:
            if user_id is not None:
                cur = conn.execute("DELETE FROM scans WHERE id = ? AND user_id = ?", (scan_id, user_id))
            else:
                cur = conn.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
            return cur.rowcount > 0
    finally:
        conn.close()


# Initialize table schemas upon module load
init_db()
