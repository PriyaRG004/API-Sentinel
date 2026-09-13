from monitor import check_api


def test_valid_api():

    result = check_api(
        "https://jsonplaceholder.typicode.com/posts/1"
    )

    assert result["status"] == "UP"
    assert result["status_code"] == 200


def test_google_api():

    result = check_api(
        "https://www.google.com"
    )

    assert result["status"] == "UP"
    assert result["status_code"] == 200


def test_invalid_api():

    result = check_api(
        "https://this-domain-definitely-does-not-exist-12345.com"
    )

    assert result["status"] == "DOWN"