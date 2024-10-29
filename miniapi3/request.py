import json
from typing import Dict


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
