import json
import re
from typing import Any, Dict, Optional
from urllib.parse import parse_qs


class Request:
    def __init__(
        self,
        method: str,
        path: str,
        headers: Dict,
        query_params: Dict,
        body: bytes,
        path_params: Dict = None,
    ):
        self.method = method
        self.path = path
        self.headers = headers
        self.query_params = query_params
        self.body = body
        self.path_params = path_params or {}

    async def json(self) -> dict:
        return json.loads(self.body.decode())

    async def text(self) -> str:
        return self.body.decode()

    async def form(self) -> dict:
        """Parse form data from request body"""
        content_type = self.headers.get("Content-Type", "").lower()

        # Handle URL-encoded form data
        if "application/x-www-form-urlencoded" in content_type:
            form_data = parse_qs(self.body.decode())
            # Convert lists to single values if only one item
            return {k: v[0] if len(v) == 1 else v for k, v in form_data.items()}

        # Handle multipart form data
        elif "multipart/form-data" in content_type:
            try:
                # Get boundary from content type
                boundary = content_type.split("boundary=")[1].strip()
                # Parse multipart form data
                parts = self.body.decode().split("--" + boundary)
                form_data = {}
                for part in parts[1:-1]:  # Skip first and last empty parts
                    if not part.strip():
                        continue
                    # Parse each part
                    try:
                        headers, content = part.strip().split("\r\n\r\n", 1)
                        if "Content-Disposition" in headers:
                            name = re.search(r'name="([^"]+)"', headers).group(1)
                            form_data[name] = content.strip()
                    except Exception:
                        continue  # Skip malformed parts
                return form_data
            except Exception as e:
                raise ValueError(f"Failed to parse multipart form data: {str(e)}")

        # Try to parse as URL-encoded even if Content-Type is not set
        try:
            form_data = parse_qs(self.body.decode())
            return {k: v[0] if len(v) == 1 else v for k, v in form_data.items()}
        except Exception:
            pass

        # If we can't parse the form data, return an empty dict
        return {}


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
        if isinstance(self.content, bytes):
            return self.content
        elif isinstance(self.content, dict):
            return json.dumps(self.content).encode()
        else:
            return str(self.content).encode()
