import requests

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

def graph_get(endpoint: str, access_token: str):
    url = f"{GRAPH_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()