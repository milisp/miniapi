import json
from typing import Union


class WebSocketConnection:
    def __init__(self, websocket):
        self.websocket = websocket
        self.is_dict = isinstance(websocket, dict)
        self.closed = False

    async def send(self, message: Union[str, dict]):
        if isinstance(message, dict):
            message = json.dumps(message)
        if self.is_dict:
            await self.websocket["send"]({"type": "websocket.send", "text": message})
        else:
            await self.websocket.send(message)

    async def receive(self) -> Union[str, dict]:
        if self.is_dict:
            message = await self.websocket["receive"]()
            return message.get("text", message)
        else:
            message = await self.websocket.receive()
            try:
                return json.loads(message)
            except json.JSONDecodeError:
                return message

    async def receive_text(self) -> str:
        if self.is_dict:
            message = await self.websocket["receive"]()
            return message.get("text", "")
        else:
            return await self.websocket.receive_text()

    async def send_text(self, message: str):
        if self.is_dict:
            await self.websocket["send"]({"type": "websocket.send", "text": message})
        else:
            await self.websocket.send_text(message)

    async def close(self):
        if self.is_dict:
            await self.websocket["send"]({"type": "websocket.close"})
        else:
            await self.websocket.close()

    async def accept(self):
        if self.is_dict:
            # Accept is handled by the handler in ASGI mode
            pass
        else:
            await self.websocket.accept()
