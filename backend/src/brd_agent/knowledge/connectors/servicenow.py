"""ServiceNow Table API client."""

from __future__ import annotations

import json
from typing import Any

import httpx

from brd_agent.core.config import get_settings


class ServiceNowConfigurationError(RuntimeError):
    pass


class ServiceNowClient:
    def __init__(
        self,
        *,
        instance_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        settings = get_settings()
        self._instance_url = (instance_url or settings.servicenow_instance_url or "").rstrip(
            "/"
        )
        self._username = username or settings.servicenow_username
        self._password = password or settings.servicenow_password
        self._timeout = timeout

    def is_configured(self) -> bool:
        return bool(self._instance_url and self._username and self._password)

    def _require_configured(self) -> None:
        if not self.is_configured():
            raise ServiceNowConfigurationError(
                "ServiceNow is not configured. Set SERVICENOW_INSTANCE_URL, "
                "SERVICENOW_USERNAME, and SERVICENOW_PASSWORD."
            )

    def _auth(self) -> tuple[str, str]:
        self._require_configured()
        return (self._username or "", self._password or "")

    def _table_url(self, table: str, sys_id: str | None = None) -> str:
        self._require_configured()
        base = f"{self._instance_url}/api/now/table/{table}"
        if sys_id:
            return f"{base}/{sys_id}"
        return base

    async def get_record(self, table: str, sys_id: str) -> dict[str, Any]:
        url = self._table_url(table, sys_id)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, auth=self._auth())
            response.raise_for_status()
            payload = response.json()
        return {"table": table, "record": payload.get("result")}

    async def query_records(
        self, table: str, query: str = "", limit: int = 10
    ) -> dict[str, Any]:
        url = self._table_url(table)
        params: dict[str, Any] = {
            "sysparm_limit": max(1, min(limit, 100)),
        }
        if query.strip():
            params["sysparm_query"] = query
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params=params, auth=self._auth())
            response.raise_for_status()
            payload = response.json()
        records = payload.get("result") or []
        return {"table": table, "query": query, "size": len(records), "records": records}

    async def create_record(self, table: str, fields: dict[str, Any]) -> dict[str, Any]:
        url = self._table_url(table)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=fields, auth=self._auth())
            response.raise_for_status()
            payload = response.json()
        return {"table": table, "record": payload.get("result")}

    async def update_record(
        self, table: str, sys_id: str, fields: dict[str, Any]
    ) -> dict[str, Any]:
        url = self._table_url(table, sys_id)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.patch(url, json=fields, auth=self._auth())
            response.raise_for_status()
            payload = response.json()
        return {"table": table, "record": payload.get("result")}


def parse_fields_json(fields_json: str) -> dict[str, Any]:
    try:
        parsed = json.loads(fields_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"fields_json must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("fields_json must decode to a JSON object")
    return parsed
