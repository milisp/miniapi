import json
from unittest.mock import AsyncMock, Mock

import pytest

from miniapi3.websocket import WebSocketConnection


@pytest.fixture
def mock_websocket():
    websocket = Mock()
    websocket.send = AsyncMock()
    websocket.receive = AsyncMock()
    return websocket


@pytest.fixture
def ws_connection(mock_websocket):
    return WebSocketConnection(mock_websocket)


@pytest.mark.asyncio
async def test_send_string_message(ws_connection, mock_websocket):
    message = "hello world"
    await ws_connection.send(message)
    mock_websocket.send.assert_awaited_once_with(message)


@pytest.mark.asyncio
async def test_send_dict_message(ws_connection, mock_websocket):
    message = {"key": "value"}
    await ws_connection.send(message)
    mock_websocket.send.assert_awaited_once_with(json.dumps(message))


@pytest.mark.asyncio
async def test_receive_string_message(ws_connection, mock_websocket):
    message = "hello world"
    mock_websocket.receive.return_value = message
    received = await ws_connection.receive()
    assert received == message


@pytest.mark.asyncio
async def test_receive_json_message(ws_connection, mock_websocket):
    message = {"key": "value"}
    mock_websocket.receive.return_value = json.dumps(message)
    received = await ws_connection.receive()
    assert received == message
