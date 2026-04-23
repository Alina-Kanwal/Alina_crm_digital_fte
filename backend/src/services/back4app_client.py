"""
Back4App (Parse Server) REST API Client.
Wraps the Parse REST API for synchronous use in repository classes.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

_APP_ID   = os.getenv("BACK4APP_APP_ID", "")
_REST_KEY = os.getenv("BACK4APP_REST_KEY", "")
_MASTER_KEY = os.getenv("BACK4APP_MASTER_KEY", "")
_API_URL  = os.getenv("BACK4APP_API_URL", "https://parseapi.back4app.com")


class ParseClient:
    """Thin synchronous wrapper around the Parse REST API."""

    def __init__(self):
        self.base_url = _API_URL
        self._headers = {
            "X-Parse-Application-Id": _APP_ID,
            "X-Parse-REST-API-Key":   _REST_KEY,
            "Content-Type":           "application/json",
        }
        self._master_headers = {
            **self._headers,
            "X-Parse-Master-Key": _MASTER_KEY,
        }

    # ------------------------------------------------------------------ #
    # Low-level helpers
    # ------------------------------------------------------------------ #

    def find(
        self,
        class_name: str,
        where: Optional[Dict] = None,
        skip: int = 0,
        limit: int = 100,
        order: str = "-createdAt",
    ) -> List[Dict]:
        """Return a list of Parse objects from a class."""
        params: Dict[str, Any] = {"limit": limit, "skip": skip, "order": order}
        if where:
            params["where"] = json.dumps(where)

        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                f"{self.base_url}/classes/{class_name}",
                headers=self._headers,
                params=params,
            )
            resp.raise_for_status()
            return resp.json().get("results", [])

    def get(self, class_name: str, object_id: str) -> Optional[Dict]:
        """Fetch a single Parse object by objectId. Returns None if not found."""
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                f"{self.base_url}/classes/{class_name}/{object_id}",
                headers=self._headers,
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()

    def create(self, class_name: str, data: Dict) -> Dict:
        """Create a Parse object. Returns the full object (with objectId, createdAt)."""
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                f"{self.base_url}/classes/{class_name}",
                headers=self._headers,
                json=data,
            )
            resp.raise_for_status()
            created = resp.json()
            # Parse returns only {objectId, createdAt} on create — re-fetch full object
            return self.get(class_name, created["objectId"]) or created

    def update(self, class_name: str, object_id: str, data: Dict) -> Dict:
        """Update a Parse object. Returns the full updated object."""
        with httpx.Client(timeout=15.0) as client:
            resp = client.put(
                f"{self.base_url}/classes/{class_name}/{object_id}",
                headers=self._headers,
                json=data,
            )
            resp.raise_for_status()
        return self.get(class_name, object_id) or {}

    def count(self, class_name: str, where: Optional[Dict] = None) -> int:
        """Return the count of objects matching a query."""
        params: Dict[str, Any] = {"count": 1, "limit": 0}
        if where:
            params["where"] = json.dumps(where)
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                f"{self.base_url}/classes/{class_name}",
                headers=self._headers,
                params=params,
            )
            resp.raise_for_status()
            return resp.json().get("count", 0)

    def is_healthy(self) -> bool:
        """Ping the Parse health endpoint."""
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(
                    f"{self.base_url}/health",
                    headers=self._headers,
                )
                return resp.status_code == 200
        except Exception:
            return False


# Module-level singleton
parse_client = ParseClient()
