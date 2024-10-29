import inspect
from typing import Callable

from ..websocket import WebSocketConnection


class WebSocketHandler:
    @staticmethod
    async def handle(app, scope: dict, receive: Callable, send: Callable) -> None:
        if app.debug:
            print(f"WebSocket scope: {scope}")
        path = scope["path"]
        if path not in app.router.websocket_handlers:
            return

        handler = app.router.websocket_handlers[path]
        websocket = WebSocketConnection({"receive": receive, "send": send})

        await send({"type": "websocket.accept"})

        if len(inspect.signature(handler).parameters) > 0:
            if app.debug:
                print(f"WebSocket handler: {handler}")
                print(f"WebSocket params: {inspect.signature(handler).parameters}")
            await handler(websocket)
        else:
            await handler()
