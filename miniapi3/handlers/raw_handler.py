import asyncio
import inspect
from urllib.parse import parse_qs

from ..parameter_resolver import ParameterResolver
from ..request import Request
from ..response import Response
from ..validation import ValidationError

try:
    from pydantic import BaseModel
except ImportError:
    BaseModel = None


class RawHandler:
    @staticmethod
    async def handle(app, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            request_line = await reader.readline()
            method, path_raw, _ = request_line.decode().strip().split()
            # Parse headers
            headers = {}
            while True:
                header_line = await reader.readline()
                if header_line == b"\r\n":
                    break
                name, value = header_line.decode().strip().split(": ", 1)
                headers[name] = value

            # Parse path before WebSocket check
            if "?" in path_raw:
                path, query_string = path_raw.split("?", 1)
                query_params = parse_qs(query_string)
            else:
                path = path_raw
                query_params = {}

            # Check if this is a WebSocket upgrade request
            if headers.get("Upgrade", "").lower() == "websocket":
                if path in app.router.websocket_handlers:
                    try:
                        import websockets
                    except ImportError:
                        raise ImportError("Websocket is not installed, please install it with `pip install websockets`")
                    websocket = await websockets.server.WebSocketServerProtocol(
                        reader=reader, writer=writer, headers=headers
                    )
                    await app._handle_websocket(websocket, path)
                    return

            # Read body if present
            content_length = int(headers.get("Content-Length", 0))
            body = await reader.read(content_length) if content_length else b""

            # Match route and extract parameters
            route_path, path_params = app.router._match_route(path)

            # Create request object
            request = Request(method, path, headers, query_params, body, path_params)
            if method == "OPTIONS":
                response = Response("", 204)
                print("resp", response)
                # 应用中间件
                for middleware in app.middleware:
                    if hasattr(middleware, "process_response"):
                        response = middleware.process_response(response, request)

                # 确保 CORS 头被写入响应
                response_bytes = "HTTP/1.1 204 No Content\r\n".encode()
                for name, value in response.headers.items():
                    response_bytes += f"{name}: {value}\r\n".encode()
                response_bytes += b"\r\n"  # 空行分隔头和主体
                writer.write(response_bytes)
                await writer.drain()
                return  # 直接返回，不继续处理

            # Route request
            elif route_path and method in app.router.routes[route_path]:
                handler = app.router.routes[route_path][method]
                try:
                    params = await ParameterResolver.resolve_params(handler, request, app.debug)
                    if app.debug:
                        print(f"Handler params resolved: {params}")

                    response = await handler(**params) if inspect.iscoroutinefunction(handler) else handler(**params)

                    if isinstance(response, (dict, str, BaseModel)):
                        response = Response(response)
                except ValidationError as e:
                    if app.debug:
                        print(f"Validation error: {str(e)}")
                    response = Response({"error": str(e)}, status=400)
                except Exception as e:
                    if app.debug:
                        print(f"Handler error: {str(e)}")
                        import traceback

                        traceback.print_exc()
                    response = Response({"error": str(e)}, status=500)
            else:
                response = Response({"error": "Not Found"}, 404)

            # 应用中间件
            for middleware in app.middleware:
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
