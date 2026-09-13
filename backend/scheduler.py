import time
import threading

from database import SessionLocal
from models import API, MonitoringCheck
from monitor import check_api


# How often APIs are checked
CHECK_INTERVAL = 60


def monitor_all_apis():
    db = SessionLocal()

    try:
        apis = (
            db.query(API)
            .filter(API.active == True)
            .all()
        )

        print("Running automatic API monitoring...")

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

            print(
                f"{api.name}: "
                f"{result['status']} "
                f"({result.get('status_code')})"
            )

        db.commit()

        print("Monitoring check completed.")

    except Exception as error:

        db.rollback()

        print("Scheduler error:", error)

    finally:

        db.close()


def scheduler_loop():

    while True:

        monitor_all_apis()

        time.sleep(CHECK_INTERVAL)


def start_scheduler():

    thread = threading.Thread(
        target=scheduler_loop,
        daemon=True
    )

    thread.start()

    print(
        f"API Sentinel scheduler started. "
        f"Checking every {CHECK_INTERVAL} seconds."
    )