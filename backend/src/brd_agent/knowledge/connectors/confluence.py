"""Atlassian Confluence REST API client."""

from __future__ import annotations

import re
from typing import Any

import httpx

from brd_agent.core.config import get_settings


class ConfluenceConfigurationError(RuntimeError):
    pass


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


class ConfluenceClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        email: str | None = None,
        api_token: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.confluence_base_url or "").rstrip("/")
        self._email = email or settings.confluence_email
        self._api_token = api_token or settings.confluence_api_token
        self._timeout = timeout

    def is_configured(self) -> bool:
        return bool(self._base_url and self._email and self._api_token)

    def _require_configured(self) -> None:
        if not self.is_configured():
            raise ConfluenceConfigurationError(
                "Confluence is not configured. Set CONFLUENCE_BASE_URL, "
                "CONFLUENCE_EMAIL, and CONFLUENCE_API_TOKEN."
            )

    def _auth(self) -> tuple[str, str]:
        self._require_configured()
        return (self._email or "", self._api_token or "")

    def _api_root(self) -> str:
        self._require_configured()
        if self._base_url.endswith("/wiki"):
            return f"{self._base_url}/rest/api"
        return f"{self._base_url}/wiki/rest/api"

    async def read_page(self, page_id: str) -> dict[str, Any]:
        url = f"{self._api_root()}/content/{page_id}"
        params = {"expand": "body.storage,version,space"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params=params, auth=self._auth())
            response.raise_for_status()
            payload = response.json()
        storage = (payload.get("body") or {}).get("storage") or {}
        html = storage.get("value") or ""
        return {
            "id": payload.get("id"),
            "title": payload.get("title"),
            "space_key": (payload.get("space") or {}).get("key"),
            "version": (payload.get("version") or {}).get("number"),
            "body_html": html,
            "body_text": _strip_html(html),
            "web_url": payload.get("_links", {}).get("webui"),
        }

    async def search(self, cql: str, limit: int = 10) -> dict[str, Any]:
        url = f"{self._api_root()}/content/search"
        params = {"cql": cql, "limit": max(1, min(limit, 50))}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params=params, auth=self._auth())
            response.raise_for_status()
            payload = response.json()
        results = []
        for item in payload.get("results", []):
            results.append(
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "type": item.get("type"),
                    "web_url": item.get("_links", {}).get("webui"),
                }
            )
        return {"cql": cql, "size": len(results), "results": results}

    async def create_page(
        self,
        *,
        space_key: str,
        title: str,
        body: str,
        parent_id: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self._api_root()}/content"
        data: dict[str, Any] = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": body,
                    "representation": "storage",
                }
            },
        }
        if parent_id:
            data["ancestors"] = [{"id": parent_id}]
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=data, auth=self._auth())
            response.raise_for_status()
            payload = response.json()
        return {
            "id": payload.get("id"),
            "title": payload.get("title"),
            "version": (payload.get("version") or {}).get("number"),
            "web_url": payload.get("_links", {}).get("webui"),
        }

    async def update_page(
        self,
        *,
        page_id: str,
        title: str,
        body: str,
        version: int,
    ) -> dict[str, Any]:
        url = f"{self._api_root()}/content/{page_id}"
        data = {
            "id": page_id,
            "type": "page",
            "title": title,
            "version": {"number": version + 1},
            "body": {
                "storage": {
                    "value": body,
                    "representation": "storage",
                }
            },
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.put(url, json=data, auth=self._auth())
            response.raise_for_status()
            payload = response.json()
        return {
            "id": payload.get("id"),
            "title": payload.get("title"),
            "version": (payload.get("version") or {}).get("number"),
            "web_url": payload.get("_links", {}).get("webui"),
        }
