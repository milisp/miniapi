import inspect
from typing import Callable
from urllib.parse import parse_qs

from ..parameter_resolver import ParameterResolver
from ..request import Request
from ..response import Response
from ..validation import ValidationError

try:
    from pydantic import BaseModel
except ImportError:
    BaseModel = None


class HTTPHandler:
    @staticmethod
    async def handle(app, scope: dict, receive: Callable, send: Callable) -> None:
        # Parse path and query from scope
        path = scope["path"]
        query_params = {}
        raw_query = scope.get("query_string", b"").decode()
        if raw_query:
            query_dict = parse_qs(raw_query)
            query_params = {
                k: [v.decode() if isinstance(v, bytes) else v for v in vals] for k, vals in query_dict.items()
            }

        headers = {k.decode(): v.decode() for k, v in scope["headers"]}

        # Read body
        body = b""
        more_body = True
        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        # Create request object
        route_path, path_params = app.router._match_route(path)
        request = Request(scope["method"], path, headers, query_params, body, path_params)

        try:
            if scope["method"] == "OPTIONS":
                response = Response("", 204)
                # Apply middleware for OPTIONS request
                for middleware in app.middleware:
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

            elif route_path and scope["method"] in app.router.routes[route_path]:
                handler = app.router.routes[route_path][scope["method"]]
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

            # Apply middleware
            for middleware in app.middleware:
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
            if app.debug:
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
