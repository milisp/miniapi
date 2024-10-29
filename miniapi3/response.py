import json
from typing import Any, Dict, Optional

try:
    from pydantic import BaseModel
except ImportError:
    BaseModel = None


class Response:
    def __init__(
        self,
        content: Any = "",
        status: int = 200,
        headers: Optional[Dict] = None,
        content_type: str = None,
    ):
        self.content = content
        self.status = status
        self.headers = headers or {}

        # Set content type
        if content_type:
            self.content_type = content_type
        elif isinstance(content, dict):
            self.content_type = "application/json"
        elif isinstance(content, str) and content.strip().startswith("<!DOCTYPE html>"):
            self.content_type = "text/html"
        else:
            self.content_type = "text/plain"

        # Ensure Content-Type is in headers
        self.headers["Content-Type"] = self.content_type

    def to_bytes(self) -> bytes:
        # Convert content to bytes based on type
        print("type", type(self.content))
        if isinstance(self.content, bytes):
            return self.content
        elif isinstance(self.content, dict):
            return json.dumps(self.content).encode()
        elif isinstance(self.content, BaseModel):
            return json.dumps(self.content.dict()).encode()
        else:
            return str(self.content).encode()
