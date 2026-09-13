from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import SessionLocal
from models import API, MonitoringCheck
from monitor import check_api
import scheduler


app = FastAPI(title="API Sentinel")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# REQUEST MODELS
# -------------------------

class APIRequest(BaseModel):
    name: str
    url: str


class APIStatusRequest(BaseModel):
    active: bool


# -------------------------
# ROOT
# -------------------------

@app.get("/")
def read_root():
    return {
        "message": "API Sentinel is running!"
    }


# -------------------------
# GET ALL APIS
# -------------------------

@app.get("/apis")
def get_apis():
    db = SessionLocal()

    try:
        apis = db.query(API).all()

        results = []

        for api in apis:

            if api.active:
                result = check_api(api.url)

                check = MonitoringCheck(
                    api_id=api.id,
                    status=result["status"],
                    status_code=result.get("status_code"),
                    response_time=result.get("response_time"),
                    error=result.get("error")
                )

                db.add(check)

                results.append({
                    "id": api.id,
                    "name": api.name,
                    "url": api.url,
                    "active": api.active,
                    **result
                })

            else:
                results.append({
                    "id": api.id,
                    "name": api.name,
                    "url": api.url,
                    "active": api.active,
                    "status": "INACTIVE",
                    "status_code": None,
                    "response_time": None
                })

        db.commit()

        return results

    finally:
        db.close()


# -------------------------
# ADD API
# -------------------------

@app.post("/apis")
def create_api(api_data: APIRequest):
    db = SessionLocal()

    try:
        new_api = API(
            name=api_data.name,
            url=api_data.url,
            active=True
        )

        db.add(new_api)
        db.commit()
        db.refresh(new_api)

        return {
            "message": "API added successfully",
            "id": new_api.id,
            "name": new_api.name,
            "url": new_api.url,
            "active": new_api.active
        }

    finally:
        db.close()


# -------------------------
# DELETE API
# -------------------------

@app.delete("/apis/{api_id}")
def delete_api(api_id: int):
    db = SessionLocal()

    try:
        api = db.query(API).filter(
            API.id == api_id
        ).first()

        if not api:
            return {
                "message": "API not found"
            }

        # Delete monitoring history first
        db.query(MonitoringCheck).filter(
            MonitoringCheck.api_id == api_id
        ).delete(
            synchronize_session=False
        )

        # Delete API
        db.delete(api)

        db.commit()

        return {
            "message": "API deleted successfully"
        }

    except Exception as error:
        db.rollback()

        print("Delete error:", error)

        return {
            "message": "Failed to delete API"
        }

    finally:
        db.close()


# -------------------------
# VIEW API HISTORY
# -------------------------

@app.get("/apis/{api_id}/history")
def get_api_history(api_id: int):
    db = SessionLocal()

    try:
        api = db.query(API).filter(
            API.id == api_id
        ).first()

        if not api:
            return {
                "message": "API not found"
            }

        checks = (
            db.query(MonitoringCheck)
            .filter(
                MonitoringCheck.api_id == api_id
            )
            .order_by(
                MonitoringCheck.checked_at.desc()
            )
            .all()
        )

        results = []

        for check in checks:

            results.append({
                "status": check.status,
                "status_code": check.status_code,
                "response_time": check.response_time,
                "error": check.error,
                "checked_at": check.checked_at
            })

        return {
            "api_id": api.id,
            "name": api.name,
            "url": api.url,
            "active": api.active,
            "history": results
        }

    finally:
        db.close()


# -------------------------
# ENABLE / DISABLE API
# -------------------------

@app.put("/apis/{api_id}")
def update_api_status(
    api_id: int,
    api_data: APIStatusRequest
):
    db = SessionLocal()

    try:
        api = db.query(API).filter(
            API.id == api_id
        ).first()

        if not api:
            return {
                "message": "API not found"
            }

        api.active = api_data.active

        db.commit()
        db.refresh(api)

        return {
            "message": (
                "API enabled successfully"
                if api.active
                else "API disabled successfully"
            ),
            "id": api.id,
            "name": api.name,
            "url": api.url,
            "active": api.active
        }

    finally:
        db.close()


# -------------------------
# DASHBOARD
# -------------------------

@app.get("/dashboard")
def get_dashboard():
    db = SessionLocal()

    try:

        # Get ALL APIs, including inactive ones
        apis = db.query(API).all()

        results = []

        total = len(apis)
        active = 0
        up = 0
        down = 0

        for api in apis:

            if api.active:

                active += 1

                latest_check = (
                    db.query(MonitoringCheck)
                    .filter(
                        MonitoringCheck.api_id == api.id
                    )
                    .order_by(
                        MonitoringCheck.checked_at.desc()
                    )
                    .first()
                )

                if latest_check:

                    status = latest_check.status
                    response_time = latest_check.response_time
                    status_code = latest_check.status_code

                else:

                    status = "UNKNOWN"
                    response_time = None
                    status_code = None

                if status == "UP":
                    up += 1

                elif status == "DOWN":
                    down += 1

            else:

                status = "INACTIVE"
                response_time = None
                status_code = None

            results.append({
                "id": api.id,
                "name": api.name,
                "url": api.url,
                "active": api.active,
                "status": status,
                "status_code": status_code,
                "response_time": response_time
            })

        return {
            "summary": {
                "total": total,
                "active": active,
                "up": up,
                "down": down
            },
            "apis": results
        }

    finally:
        db.close()