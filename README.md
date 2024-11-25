# MiniAPI3

A lightweight Python web framework inspired by FastAPI, featuring async support, WebSocket capabilities, and middleware.

## github repo 

[miniapi3](https://github.com/milisp/miniapi) ![PyPI Downloads](https://static.pepy.tech/badge/miniapi3)

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
# main.py
from miniapi3 import MiniAPI, Request

app = MiniAPI()

@app.get("/")
async def hello():
    return {"message": "Hello, World!"}

@app.get("/users/{user_id}")
async def get_user(request: Request):
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

## uvicorn support

```bash
uvicorn main:app
```

## Request Validation

```bash
pip install pydantic
```

```python
from miniapi3 import MiniAPI
from pydantic import BaseModel

app = MiniAPI()

class UserCreate(BaseModel):
    name: str

@app.post("/users")
async def create_user(user: UserCreate):
    return dict(user)
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
