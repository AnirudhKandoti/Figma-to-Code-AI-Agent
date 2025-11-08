from __future__ import annotations
import requests
from typing import Any, Dict, List

FIGMA_BASE = "https://api.figma.com/v1"

class FigmaAPI:
    def __init__(self, token: str, timeout: int = 30):
        # Use ONLY X-Figma-Token since Bearer fails in your environment
        self._headers = {
            "X-Figma-Token": token,
            "User-Agent": "figma-to-code-ai-agent/0.1",
        }
        self._timeout = timeout

    def _get(self, url: str, **params) -> Dict[str, Any]:
        r = requests.get(url, headers=self._headers, params=params or None, timeout=self._timeout)
        if r.status_code != 200:
            raise RuntimeError(f"Figma API error {r.status_code} at {url}:\n{r.text}")
        return r.json()

    def get_file(self, file_id: str) -> Dict[str, Any]:
        return self._get(f"{FIGMA_BASE}/files/{file_id}")

    def get_images(self, file_id: str, node_ids: List[str], scale: int = 2) -> Dict[str, Any]:
        ids = ",".join(node_ids)
        return self._get(f"{FIGMA_BASE}/images/{file_id}", ids=ids, scale=scale)
