# MiniAPI

A lightweight Python web framework inspired by FastAPI, featuring async support, WebSocket capabilities, and middleware.

## Features

- Async request handling
- Route parameters
- WebSocket support
- Middleware system
- Request validation
- CORS support
- Form data handling
- ASGI compatibility

## Installation

```bash
pip install miniapi3
```

For WebSocket support:
```bash
pip install miniapi3[websockets]
```

## Quick Start
```python
from miniapi3 import MiniAPI, Response

app = MiniAPI()

@app.get("/")
async def hello():
    return {"message": "Hello, World!"}

@app.get("/users/{user_id}")
async def get_user(request):
    user_id = request.path_params["user_id"]
    return {"user_id": user_id}

# WebSocket example
@app.websocket("/ws")
async def websocket_handler(ws):
    while True:
        message = await ws.receive()
        await ws.send(f"Echo: {message}")

if __name__ == "__main__":
    app.run()
```


## Request Validation

```python
from dataclasses import dataclass

from miniapi3.validation import RequestValidator, ValidationError
from miniapi3 import MiniAPI, Response

app = MiniAPI()

@dataclass
class UserCreate(RequestValidator):
    username: str
    email: str
    age: int

@app.post("/users")
@app.validate(UserCreate)
async def create_user(request, data: UserCreate):
    return {"user": data}
```


## CORS Middleware

```python
from miniapi3 import MiniAPI, CORSMiddleware

app = MiniAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```


## HTML Response

```python
from miniapi3 import MiniAPI, html

app = MiniAPI()

@app.get("/")
async def index():
    return html("<h1>Hello, World!</h1>")
```
