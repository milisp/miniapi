import json
from typing import Union


class WebSocketConnection:
    def __init__(self, websocket):
        self.websocket = websocket

    async def send(self, message: Union[str, dict]):
        if isinstance(message, dict):
            message = json.dumps(message)
        await self.websocket.send(message)

    async def receive(self) -> Union[str, dict]:
        message = await self.websocket.receive()
        try:
            return json.loads(message)
        except json.JSONDecodeError:
            return message
