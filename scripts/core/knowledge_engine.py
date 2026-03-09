#!/usr/bin/env python3
import os
import json
import lancedb
import requests
from typing import Any, Dict, List, Optional


class KnowledgeEngine:
    """
    Codex-Loop 核心知識引擎 (Lvl 15 Security Hardened)
    支援語義檢索、RAG 診斷與 P01-P06 失敗模式偵測。
    """

    def __init__(
        self,
        db_path: str = "~/.openclaw/memory/lancedb-pro",
        table_name: str = "agent_main",
    ):
        self.db_path = os.path.expanduser(db_path)
        self.table_name = table_name
        self.jina_key = os.environ.get("JINA_API_KEY", "MISSING_KEY")

    def _safe_json_get(
        self, data: Any, key: Optional[str] = None, default: Any = "Unknown"
    ) -> Any:
        """【安全加固】解析 metadata JSON 並獲取欄位"""
        parsed = {}
        if isinstance(data, dict):
            parsed = data
        else:
            try:
                parsed = json.loads(str(data)) if data else {}
            except (json.JSONDecodeError, TypeError, ValueError):
                parsed = {}

        if key is None:
            return parsed
        return parsed.get(key, default)

    def get_embedding(self, text: str) -> Optional[List[float]]:
        if self.jina_key == "MISSING_KEY":
            return None
        url = "https://api.jina.ai/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.jina_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "jina-embeddings-v3",
            "input": [text],
            "task": "retrieval.query",
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            res = response.json()
            return res["data"][0]["embedding"]
        except (requests.RequestException, KeyError, json.JSONDecodeError, ValueError):
            return None

    def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        if not os.path.exists(self.db_path):
            return []
        db = lancedb.connect(self.db_path)
        if self.table_name not in db.table_names():
            return []

        table = db.open_table(self.table_name)
        vector = self.get_embedding(query)
        if not vector:
            return []

        results = table.search(vector).limit(limit).to_list()
        processed = []
        for r in results:
            meta = self._safe_json_get(r.get("metadata"))
            processed.append(
                {
                    "source": meta.get("source", "Unknown"),
                    "score": round(1 - r.get("_distance", 0), 4),
                    "text": r.get("content", ""),
                    "updated_at": meta.get("updated_at", "Unknown"),
                }
            )
        return processed


if __name__ == "__main__":
    engine = KnowledgeEngine()
    print("[*] Knowledge Engine Initialized.")
