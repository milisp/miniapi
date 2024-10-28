import asyncio
import inspect
import json
import re
from dataclasses import dataclass
from typing import Callable, Dict, Optional
from urllib.parse import parse_qs

from .http import Request, Response
from .validation import ValidationError
from .websocket import WebSocketConnection


@dataclass
class URLPattern:
    path: str
    pattern: re.Pattern
    param_names: list[str]


class MiniAPI:
    def __init__(self):
        self.routes: Dict[str, Dict[str, Callable]] = {}
        self.url_patterns: Dict[str, URLPattern] = {}
        self.websocket_handlers: Dict[str, Callable] = {}
        self.middleware = []
        self.debug = False

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

    def add_middleware(self, middleware):
        """添加中间件"""
        self.middleware.append(middleware)

    def _route(self, path: str, methods: list):
        """Internal route registration with URL pattern support"""
        # 检查是否包含URL数
        param_pattern = r"{([^{}]+)}"
        param_names = re.findall(param_pattern, path)
        if param_names:
            # 将URL参数转换为正则表达式
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
        # 首先检查精确匹配
        if path in self.routes:
            return path, {}

        # 然后检查模式匹配
        for url_pattern in self.url_patterns.values():
            match = url_pattern.pattern.match(path)
            if match:
                params = dict(zip(url_pattern.param_names, match.groups()))
                return url_pattern.path, params

        return None, None

    async def _handle_websocket(self, websocket, path):
        """Handle WebSocket connections"""
        if path in self.websocket_handlers:
            handler = self.websocket_handlers[path]
            conn = WebSocketConnection(websocket)
            # Check if handler accepts connection parameter
            if len(inspect.signature(handler).parameters) > 0:
                await handler(conn)
            else:
                await handler()

    async def handle_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            print("start request")
            request_line = await reader.readline()
            method, path_raw, _ = request_line.decode().strip().split()
            print("m", path_raw)
            # Parse headers
            headers = {}
            while True:
                header_line = await reader.readline()
                if header_line == b"\r\n":
                    break
                name, value = header_line.decode().strip().split(": ", 1)
                headers[name] = value
            print("head", headers)

            # Parse path before WebSocket check
            if "?" in path_raw:
                path, query_string = path_raw.split("?", 1)
                query_params = parse_qs(query_string)
            else:
                path = path_raw
                query_params = {}

            # Check if this is a WebSocket upgrade request
            if headers.get("Upgrade", "").lower() == "websocket":
                if path in self.websocket_handlers:
                    try:
                        import websockets
                    except ImportError:
                        raise ImportError("Websocket is not installed, please install it with `pip install websockets`")
                    websocket = await websockets.server.WebSocketServerProtocol(
                        reader=reader, writer=writer, headers=headers
                    )
                    await self._handle_websocket(websocket, path)
                    return

            # Read body if present
            content_length = int(headers.get("Content-Length", 0))
            body = await reader.read(content_length) if content_length else b""

            # Match route and extract parameters
            route_path, path_params = self._match_route(path)

            # Create request object
            request = Request(method, path, headers, query_params, body, path_params)
            print("method", method)
            if method == "OPTIONS":
                response = Response("", 204)
                print("resp", response)
                # 应用中间件
                for middleware in self.middleware:
                    if hasattr(middleware, "process_response"):
                        response = middleware.process_response(response, request)

                print("bye")
                # 确保 CORS 头被写入响应
                response_bytes = "HTTP/1.1 204 No Content\r\n".encode()
                for name, value in response.headers.items():
                    response_bytes += f"{name}: {value}\r\n".encode()
                response_bytes += b"\r\n"  # 空行分隔头和主体
                writer.write(response_bytes)
                await writer.drain()
                return  # 直接返回，不继续处理

            # Route request
            elif route_path and method in self.routes[route_path]:
                handler = self.routes[route_path][method]
                try:
                    params = await self._resolve_params(handler, request)
                    if self.debug:
                        print(f"Handler params resolved: {params}")

                    response = await handler(**params) if inspect.iscoroutinefunction(handler) else handler(**params)

                    if isinstance(response, (dict, str)):
                        response = Response(response)
                except ValidationError as e:
                    if self.debug:
                        print(f"Validation error: {str(e)}")
                    response = Response({"error": str(e)}, status=400)
                except Exception as e:
                    if self.debug:
                        print(f"Handler error: {str(e)}")
                        import traceback

                        traceback.print_exc()
                    response = Response({"error": str(e)}, status=500)
            else:
                response = Response({"error": "Not Found"}, 404)

            # 应用中间件
            for middleware in self.middleware:
                print("mid", middleware)
                if hasattr(middleware, "process_response"):
                    print("resp", response)
                    response = middleware.process_response(response, request)

            # Format response with proper HTTP/1.1 status line and headers
            status_text = {
                200: "OK",
                201: "Created",
                400: "Bad Request",
                401: "Unauthorized",
                403: "Forbidden",
                404: "Not Found",
                500: "Internal Server Error",
            }.get(response.status, "Unknown")
            print("status", response.status)
            response_bytes = f"HTTP/1.1 {response.status} {status_text}\r\n".encode()

            # Add headers
            for name, value in response.headers.items():
                response_bytes += f"{name}: {value}\r\n".encode()
            response_bytes += "\r\n".encode()  # Empty line to separate headers from body

            # Add body
            response_bytes += response.to_bytes()
            print("resp bye", response_bytes)
            writer.write(response_bytes)
            await writer.drain()

        except Exception as e:
            error_response = Response({"error": str(e)}, 500)
            # Format error response with proper HTTP/1.1 status line
            error_bytes = "HTTP/1.1 500 Internal Server Error\r\n".encode()
            error_bytes += error_response.to_bytes()
            writer.write(error_bytes)
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        """ASGI application interface"""
        if scope["type"] == "http":
            await self._handle_asgi_http(scope, receive, send)
        elif scope["type"] == "websocket":
            await self._handle_asgi_websocket(scope, receive, send)
        else:
            raise ValueError(f"Unknown scope type: {scope['type']}")

    async def _handle_asgi_http(self, scope: dict, receive: Callable, send: Callable) -> None:
        # Parse path and query from scope
        # url_info = urlparse(scope.get("query_string", b"").decode())
        path = scope["path"]
        # Convert query string to dictionary properly
        query_params = {}
        raw_query = scope.get("query_string", b"").decode()
        if raw_query:
            query_dict = parse_qs(raw_query)
            # Convert bytes to str if needed
            query_params = {
                k: [v.decode() if isinstance(v, bytes) else v for v in vals] for k, vals in query_dict.items()
            }

        # Get headers from scope
        headers = {k.decode(): v.decode() for k, v in scope["headers"]}

        # Read body
        body = b""
        more_body = True
        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        # Create request object
        route_path, path_params = self._match_route(path)
        request = Request(scope["method"], path, headers, query_params, body, path_params)

        try:
            if scope["method"] == "OPTIONS":
                response = Response("", 204)
                # Apply middleware for OPTIONS request
                for middleware in self.middleware:
                    if hasattr(middleware, "process_response"):
                        response = middleware.process_response(response, request)

                # Convert response to ASGI format with CORS headers
                headers = [(k.encode(), v.encode()) for k, v in response.headers.items()]
                await send(
                    {
                        "type": "http.response.start",
                        "status": response.status,
                        "headers": headers,
                    }
                )
                await send({"type": "http.response.body", "body": b""})
                return

            elif route_path and scope["method"] in self.routes[route_path]:
                handler = self.routes[route_path][scope["method"]]
                try:
                    params = await self._resolve_params(handler, request)
                    if self.debug:
                        print(f"Handler params resolved: {params}")

                    response = await handler(**params) if inspect.iscoroutinefunction(handler) else handler(**params)

                    if isinstance(response, (dict, str)):
                        response = Response(response)
                except ValidationError as e:
                    if self.debug:
                        print(f"Validation error: {str(e)}")
                    response = Response({"error": str(e)}, status=400)
                except Exception as e:
                    if self.debug:
                        print(f"Handler error: {str(e)}")
                        import traceback

                        traceback.print_exc()
                    response = Response({"error": str(e)}, status=500)
            else:
                response = Response({"error": "Not Found"}, 404)

            # Apply middleware
            for middleware in self.middleware:
                if hasattr(middleware, "process_response"):
                    response = middleware.process_response(response, request)

            # Convert response to ASGI format
            response_bytes = response.to_bytes()
            headers = [(k.encode(), v.encode()) for k, v in response.headers.items()]
            headers.append((b"content-length", str(len(response_bytes)).encode()))

            # Send response
            await send(
                {
                    "type": "http.response.start",
                    "status": response.status,
                    "headers": headers,
                }
            )
            await send({"type": "http.response.body", "body": response_bytes})

        except Exception as e:
            if self.debug:
                print(f"ASGI handler error: {str(e)}")
                import traceback

                traceback.print_exc()
            error_response = Response({"error": str(e)}, 500)
            error_bytes = error_response.to_bytes()
            await send(
                {
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await send({"type": "http.response.body", "body": error_bytes})

    async def _handle_asgi_websocket(self, scope: dict, receive: Callable, send: Callable) -> None:
        path = scope["path"]
        if path not in self.websocket_handlers:
            return

        handler = self.websocket_handlers[path]
        websocket = WebSocketConnection({"receive": receive, "send": send})

        await send({"type": "websocket.accept"})

        if len(inspect.signature(handler).parameters) > 0:
            await handler(websocket)
        else:
            await handler()

    def run(self, host: str = "127.0.0.1", port: int = 8000):
        asyncio.get_event_loop().run_until_complete(self._run(host, port))

    async def _run(self, host: str, port: int):
        server = await asyncio.start_server(self.handle_request, host, port)
        print(f"Server running on http://{host}:{port}")
        async with server:
            await server.serve_forever()

    async def _resolve_params(self, handler, request: Request):
        sig = inspect.signature(handler)
        params = {}

        try:
            if self.debug:
                print(f"Handler parameters: {sig.parameters}")
                print(f"Request body: {await request.text()}")
                print(f"Query params: {request.query_params}")

            for name, param in sig.parameters.items():
                annotation = param.annotation

                if self.debug:
                    print(f"Processing parameter {name} with annotation {annotation}")

                # Handle path parameters
                if name in request.path_params:
                    value = request.path_params[name]
                    if annotation != inspect.Parameter.empty:
                        try:
                            value = annotation(value)
                        except ValueError as e:
                            raise ValidationError(f"Invalid type for parameter {name}: {str(e)}")
                    params[name] = value
                    continue

                # Handle query parameters
                if name in request.query_params:
                    value = request.query_params[name][0]  # Get first value
                    if annotation != inspect.Parameter.empty:
                        try:
                            value = annotation(value)
                        except ValueError as e:
                            raise ValidationError(f"Invalid type for parameter {name}: {str(e)}")
                    params[name] = value
                    continue

                # Handle request object injection
                if annotation == Request:
                    params[name] = request
                    continue

                # Handle Pydantic models
                if hasattr(annotation, "model_validate"):
                    try:
                        if not hasattr(request, "_cached_json"):
                            request._cached_json = await request.json()
                        data = request._cached_json
                        params[name] = annotation.model_validate(data)
                        continue
                    except json.JSONDecodeError:
                        raise ValidationError("Invalid JSON data")
                    except Exception as e:
                        raise ValidationError(f"Validation error for {name}: {str(e)}")

                # If parameter is required but not found, raise an error
                if param.default == inspect.Parameter.empty:
                    raise ValidationError(f"Missing required parameter: {name}")

            if self.debug:
                print(f"Final resolved params: {params}")

            return params
        except Exception as e:
            if self.debug:
                print(f"Error in _resolve_params: {str(e)}")
            raise
