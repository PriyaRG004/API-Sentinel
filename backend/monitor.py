import requests
import time


def check_api(url):
    start_time = time.time()

    try:
        response = requests.get(url, timeout=10)
        response_time = time.time() - start_time

        if response.status_code == 200:
            status = "UP"
        else:
            status = "DOWN"

        return {
            "status": status,
            "status_code": response.status_code,
            "response_time": response_time,
            "error": None
        }

    except requests.exceptions.RequestException as error:
        return {
            "status": "DOWN",
            "status_code": None,
            "response_time": None,
            "error": str(error)
        }