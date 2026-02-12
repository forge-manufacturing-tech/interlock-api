from typing import Any

import requests

BASE_URL = "http://127.0.0.1:8000"


def check_health() -> bool:
    try:
        response = requests.get(f"{BASE_URL}/")
        return response.status_code == 200
    except requests.RequestException:
        return False


def ingest_bom(file_obj) -> dict[str, Any]:
    files = {"file": (file_obj.name, file_obj, "application/octet-stream")}
    try:
        response = requests.post(f"{BASE_URL}/ingest/bom", files=files)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def chat_agent(message: str) -> dict[str, Any]:
    params = {"message": message}
    try:
        response = requests.post(f"{BASE_URL}/agent/chat", params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def get_parts(limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    params = {"limit": limit, "offset": offset}
    try:
        response = requests.get(f"{BASE_URL}/parts", params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []


def get_part_details(part_id: str) -> dict[str, Any] | None:
    try:
        response = requests.get(f"{BASE_URL}/parts/{part_id}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def get_trees() -> list[dict[str, Any]]:
    try:
        response = requests.get(f"{BASE_URL}/trees")
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []


def get_tree_structure(part_id: str) -> dict[str, Any]:
    try:
        response = requests.get(f"{BASE_URL}/trees/{part_id}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {}
