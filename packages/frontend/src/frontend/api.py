from typing import Any

import requests

BASE_URL = "http://127.0.0.1:8000"


def _auth_headers(token: str | None = None) -> dict[str, str]:
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def signup(email: str, password: str, name: str | None = None) -> dict[str, Any]:
    payload = {"email": email, "password": password}
    if name:
        payload["name"] = name
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return {"error": detail}


def login(email: str, password: str) -> dict[str, Any]:
    payload = {"email": email, "password": password}
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return {"error": detail}


def get_me(token: str) -> dict[str, Any] | None:
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=_auth_headers(token))
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def create_api_key(token: str, name: str) -> dict[str, Any]:
    try:
        response = requests.post(
            f"{BASE_URL}/auth/api-keys",
            json={"name": name},
            headers=_auth_headers(token),
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def list_api_keys(token: str) -> list[dict[str, Any]]:
    try:
        response = requests.get(
            f"{BASE_URL}/auth/api-keys",
            headers=_auth_headers(token),
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []


def revoke_api_key(token: str, key_id: str) -> dict[str, Any]:
    try:
        response = requests.delete(
            f"{BASE_URL}/auth/api-keys/{key_id}",
            headers=_auth_headers(token),
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def check_health() -> bool:
    try:
        response = requests.get(f"{BASE_URL}/")
        return response.status_code == 200
    except requests.RequestException:
        return False


def ingest_bom(file_obj, token: str | None = None) -> dict[str, Any]:
    files = {"file": (file_obj.name, file_obj, "application/octet-stream")}
    try:
        response = requests.post(
            f"{BASE_URL}/ingest/bom",
            files=files,
            headers=_auth_headers(token),
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def chat_agent(message: str, token: str | None = None) -> dict[str, Any]:
    params = {"message": message}
    try:
        response = requests.post(
            f"{BASE_URL}/agent/chat",
            params=params,
            headers=_auth_headers(token),
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def get_parts(limit: int = 100, offset: int = 0, token: str | None = None) -> list[dict[str, Any]]:
    params = {"limit": limit, "offset": offset}
    try:
        response = requests.get(
            f"{BASE_URL}/parts",
            params=params,
            headers=_auth_headers(token),
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []


def get_part_details(part_id: str, token: str | None = None) -> dict[str, Any] | None:
    try:
        response = requests.get(
            f"{BASE_URL}/parts/{part_id}",
            headers=_auth_headers(token),
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def get_trees(token: str | None = None) -> list[dict[str, Any]]:
    try:
        response = requests.get(
            f"{BASE_URL}/trees",
            headers=_auth_headers(token),
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []


def get_tree_structure(part_id: str, token: str | None = None) -> dict[str, Any]:
    try:
        response = requests.get(
            f"{BASE_URL}/trees/{part_id}",
            headers=_auth_headers(token),
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {}
