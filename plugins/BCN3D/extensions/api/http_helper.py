import requests
from types import SimpleNamespace


def get(url, headers=None):
    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError:
        response = SimpleNamespace(status_code=-1)
    except Exception as e:
        response = SimpleNamespace(status_code=0)

    return response


def post(url, body, headers=None, files=None):
    if headers is None:
        headers = {}
    try:
        if not files:
            response = requests.post(url, json=body, headers=headers, files=files)
        else:
            response = requests.post(url, data=body, headers=headers, files=files)
    except requests.exceptions.ConnectionError:
        response = SimpleNamespace(status_code=-1)
    except Exception as e:
        response = SimpleNamespace(status_code=0)

    return response
