from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.db import delete_scan, get_scan, list_scans, save_scan
from app.routers.auth import get_current_user_optional

router = APIRouter(prefix="/history", tags=["history"])


class SaveScanRequest(BaseModel):
    scan_data: dict[str, Any]
    notes: Optional[str] = ""


@router.get("")
async def get_history(
    limit: int = 50,
    authorization: Optional[str] = Header(None),
):
    user = get_current_user_optional(authorization)
    user_id = user["id"] if user else None
    scans = list_scans(user_id=user_id, limit=limit)
    return {"status": "ok", "count": len(scans), "scans": scans}


@router.get("/{scan_id}")
async def get_single_scan(
    scan_id: int,
    authorization: Optional[str] = Header(None),
):
    scan = get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    user = get_current_user_optional(authorization)
    if scan.get("user_id") and (not user or user["id"] != scan["user_id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    return {"status": "ok", "scan": scan}


@router.post("")
async def save_new_scan(
    body: SaveScanRequest,
    authorization: Optional[str] = Header(None),
):
    user = get_current_user_optional(authorization)
    user_id = user["id"] if user else None
    scan_data = body.scan_data
    if body.notes:
        scan_data["notes"] = body.notes
    res = save_scan(scan_data, user_id=user_id)
    return {"status": "ok", "saved_scan": res}


@router.delete("/{scan_id}")
async def remove_scan(
    scan_id: int,
    authorization: Optional[str] = Header(None),
):
    user = get_current_user_optional(authorization)
    user_id = user["id"] if user else None
    deleted = delete_scan(scan_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scan not found or permission denied")
    return {"status": "ok", "message": f"Scan #{scan_id} deleted successfully"}
