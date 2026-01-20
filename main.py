from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
import requests

app = FastAPI()

# -------------------------
# ENV VARIABLES
# -------------------------
FORM_LINK = os.getenv("FORM_LINK")  # REQUIRED
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")  # add later

if not FORM_LINK:
    raise RuntimeError("FORM_LINK environment variable is missing")

# -------------------------
# MODELS
# -------------------------

class User(BaseModel):
    profile_name: str
    email: EmailStr
    phone: Optional[str] = None

class Meta(BaseModel):
    source: Optional[str] = "nextjs"
    request_id: Optional[str]
    timestamp: Optional[str]

class AutomationRequest(BaseModel):
    event: str
    user: User
    meta: Optional[Meta] = None

# -------------------------
# API ENDPOINT
# -------------------------

@app.post("/automation/send-access-email")
def send_access_email(payload: AutomationRequest):

    # Validate event
    if payload.event != "send_user_access_email":
        raise HTTPException(status_code=400, detail="Invalid event")

    # Build payload FOR MAKE (or logging for now)
    final_payload = {
        "event": payload.event,
        "user": payload.user.dict(),
        "access": {
            "form_link": FORM_LINK,
            "login_type": "email"
        },
        "meta": payload.meta.dict() if payload.meta else {}
    }

    # ---- TEMP: until Make is connected ----
    # Just return payload to verify correctness
    if not MAKE_WEBHOOK_URL:
        return {
            "status": "ok",
            "message": "Backend working, Make not connected yet",
            "data": final_payload
        }

    # ---- When Make is ready ----
    response = requests.post(
        MAKE_WEBHOOK_URL,
        json=final_payload,
        timeout=10
    )

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Make webhook failed")

    return {
        "status": "success",
        "request_id": payload.meta.request_id if payload.meta else None
    }
