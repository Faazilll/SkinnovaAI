from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr

from app.db import authenticate_user, get_user_by_id, register_user, verify_token

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = ""


class LoginRequest(BaseModel):
    email: str
    password: str


def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    token = parts[1] if len(parts) == 2 and parts[0].lower() == "bearer" else authorization
    payload = verify_token(token)
    if not payload:
        return None
    return get_user_by_id(payload.get("uid"))


def get_current_user_required(authorization: Optional[str] = Header(None)) -> dict:
    user = get_current_user_optional(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required or token expired")
    return user


@router.post("/register")
async def register(body: RegisterRequest):
    try:
        user_info = register_user(body.email, body.password, body.name or "")
        return {
            "status": "ok",
            "token": user_info["token"],
            "user": {
                "id": user_info["id"],
                "email": user_info["email"],
                "name": user_info["name"],
                "created_at": user_info["created_at"],
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/login")
async def login(body: LoginRequest):
    try:
        user_info = authenticate_user(body.email, body.password)
        return {
            "status": "ok",
            "token": user_info["token"],
            "user": {
                "id": user_info["id"],
                "email": user_info["email"],
                "name": user_info["name"],
                "created_at": user_info["created_at"],
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


@router.get("/me")
async def me(authorization: Optional[str] = Header(None)):
    user = get_current_user_required(authorization)
    return {"status": "ok", "user": user}


@router.post("/logout")
async def logout():
    return {"status": "ok", "message": "Logged out successfully"}
