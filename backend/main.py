from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import SessionLocal
from models import API, MonitoringCheck
from monitor import check_api
import scheduler


app = FastAPI(title="API Sentinel")
@app.on_event("startup")
def start_background_scheduler():
    scheduler.start_scheduler()


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

class APIRequest(BaseModel):
    name: str
    url: str


class APIStatusRequest(BaseModel):
    active: bool


# --------------------------------------------------
# ROOT
# --------------------------------------------------

@app.get("/")
def read_root():
    return {
        "message": "API Sentinel is running!"
    }


# --------------------------------------------------
# GET ALL ACTIVE APIs + MONITOR THEM
# --------------------------------------------------

@app.get("/apis")
def get_apis():

    db = SessionLocal()

    try:

        apis = (
            db.query(API)
            .filter(API.active == True)
            .all()
        )

        results = []

        for api in apis:

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

        db.commit()

        return results

    finally:

        db.close()


# --------------------------------------------------
# ADD NEW API
# --------------------------------------------------

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


# --------------------------------------------------
# DELETE API
# --------------------------------------------------

@app.delete("/apis/{api_id}")
def delete_api(api_id: int):

    db = SessionLocal()

    try:

        api = (
            db.query(API)
            .filter(API.id == api_id)
            .first()
        )

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


# --------------------------------------------------
# API HISTORY
# --------------------------------------------------

@app.get("/apis/{api_id}/history")
def get_api_history(api_id: int):

    db = SessionLocal()

    try:

        api = (
            db.query(API)
            .filter(API.id == api_id)
            .first()
        )

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


# --------------------------------------------------
# ACTIVATE / DEACTIVATE API
# --------------------------------------------------

@app.put("/apis/{api_id}")
def update_api(
    api_id: int,
    api_data: APIStatusRequest
):

    db = SessionLocal()

    try:

        api = (
            db.query(API)
            .filter(API.id == api_id)
            .first()
        )

        if not api:

            return {
                "message": "API not found"
            }

        api.active = api_data.active

        db.commit()

        db.refresh(api)

        return {
            "message": "API status updated",
            "id": api.id,
            "name": api.name,
            "active": api.active
        }

    finally:

        db.close()


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

@app.get("/summary")
def get_summary():

    db = SessionLocal()

    try:

        apis = (
            db.query(API)
            .filter(API.active == True)
            .all()
        )

        total = len(apis)

        up = 0
        down = 0

        for api in apis:

            result = check_api(api.url)

            if result["status"] == "UP":

                up += 1

            else:

                down += 1

        return {
            "total_apis": total,
            "up": up,
            "down": down
        }

    finally:

        db.close()


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.get("/dashboard")
def get_dashboard():

    db = SessionLocal()

    try:

        # Get ALL APIs, including inactive APIs
        apis = db.query(API).all()

        results = []

        up = 0
        down = 0
        active_count = 0

        for api in apis:

            # -----------------------------------------
            # INACTIVE API
            # -----------------------------------------

            if not api.active:

                results.append({
                    "id": api.id,
                    "name": api.name,
                    "url": api.url,
                    "active": False,
                    "status": "INACTIVE",
                    "status_code": None,
                    "response_time": None
                })

                continue

            # -----------------------------------------
            # ACTIVE API
            # -----------------------------------------

            active_count += 1

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

                response_time = (
                    latest_check.response_time
                )

                status_code = (
                    latest_check.status_code
                )

            else:

                result = check_api(api.url)

                status = result["status"]

                response_time = (
                    result.get("response_time")
                )

                status_code = (
                    result.get("status_code")
                )

            if status == "UP":
                up += 1

            elif status == "DOWN":
                down += 1

            results.append({
                "id": api.id,
                "name": api.name,
                "url": api.url,
                "active": True,
                "status": status,
                "status_code": status_code,
                "response_time": response_time
            })

        return {
            "summary": {
                "total": len(apis),
                "active": active_count,
                "up": up,
                "down": down
            },
            "apis": results
        }

    finally:

        db.close()