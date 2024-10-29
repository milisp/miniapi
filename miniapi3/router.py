import re
from dataclasses import dataclass
from typing import Callable, Dict, Optional


@dataclass
class URLPattern:
    path: str
    pattern: re.Pattern
    param_names: list[str]


class Router:
    def __init__(self):
        self.routes: Dict[str, Dict[str, Callable]] = {}
        self.url_patterns: Dict[str, URLPattern] = {}
        self.websocket_handlers: Dict[str, Callable] = {}

    def get(self, path: str):
        return self._route(path, ["GET"])

    def post(self, path: str):
        return self._route(path, ["POST"])

    def put(self, path: str):
        return self._route(path, ["PUT"])

    def delete(self, path: str):
        return self._route(path, ["DELETE"])

    def websocket(self, path: str):
        """WebSocket route decorator"""

        def decorator(handler):
            self.websocket_handlers[path] = handler
            return handler

        return decorator

    def _route(self, path: str, methods: list):
        """Internal route registration with URL pattern support"""
        param_pattern = r"{([^{}]+)}"
        param_names = re.findall(param_pattern, path)
        if param_names:
            regex_path = re.sub(param_pattern, r"([^/]+)", path)
            pattern = re.compile(f"^{regex_path}$")
            self.url_patterns[path] = URLPattern(path, pattern, param_names)

        def decorator(handler):
            if path not in self.routes:
                self.routes[path] = {}
            for method in methods:
                self.routes[path][method.upper()] = handler
            return handler

        return decorator

    def _match_route(self, path: str) -> tuple[Optional[str], Optional[dict]]:
        """Match URL pattern and extract parameters"""
        # First check exact matches
        if path in self.routes:
            return path, {}

        # Then check pattern matches
        for url_pattern in self.url_patterns.values():
            match = url_pattern.pattern.match(path)
            if match:
                params = dict(zip(url_pattern.param_names, match.groups()))
                return url_pattern.path, params

        return None, None
