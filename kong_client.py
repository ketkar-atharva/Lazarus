"""
kong_client.py — Async helpers for Kong Admin API integration.

Provides functions to register services/routes and decommission
services via Kong's request-termination plugin.
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

KONG_ADMIN_URL = os.getenv("KONG_ADMIN_URL", "http://localhost:8001")


async def register_service(api_id: str, upstream_url: str) -> dict:
    """
    Register a new service in Kong.

    POST /services  →  {"name": api_id, "url": upstream_url}
    Ignores 409 Conflict (service already exists).
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{KONG_ADMIN_URL}/services",
            json={"name": api_id, "url": upstream_url},
        )
        if resp.status_code == 409:
            return {"status": "already_exists", "api_id": api_id}
        resp.raise_for_status()
        return resp.json()


async def register_route(api_id: str, path: str, methods: list[str]) -> dict:
    """
    Attach a route to an existing Kong service.

    POST /services/{api_id}/routes  →  {"paths": [path], "methods": methods}
    Ignores 409 Conflict (route already exists).
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{KONG_ADMIN_URL}/services/{api_id}/routes",
            json={"paths": [path], "methods": methods},
        )
        if resp.status_code == 409:
            return {"status": "already_exists", "api_id": api_id, "path": path}
        resp.raise_for_status()
        return resp.json()


async def decommission_service(api_id: str) -> dict:
    """
    Apply the request-termination plugin to a Kong service so it
    returns 410 Gone with a decommission message.

    POST /services/{api_id}/plugins  →  {
        "name": "request-termination",
        "config": {"status_code": 410, "message": "Decommissioned by Lazarus"}
    }
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{KONG_ADMIN_URL}/services/{api_id}/plugins",
            json={
                "name": "request-termination",
                "config": {
                    "status_code": 410,
                    "message": "Decommissioned by Lazarus",
                },
            },
        )
        resp.raise_for_status()
        return resp.json()
