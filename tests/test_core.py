import json

import pytest

from miniapi3 import MiniAPI, Request, Response


@pytest.fixture
def app():
    return MiniAPI()


async def test_basic_routing(app):
    @app.get("/hello")
    async def hello(request):
        return {"message": "Hello, World!"}

    request = Request(method="GET", path="/hello", headers={}, query_params={}, body=b"")

    route_path, params = app._match_route("/hello")
    handler = app.routes[route_path]["GET"]
    result = await handler(request)

    # Convert dict to Response if needed
    response = result if isinstance(result, Response) else Response(result)

    assert isinstance(response, Response)
    assert response.status == 200
    assert json.loads(response.to_bytes()) == {"message": "Hello, World!"}


async def test_path_parameters(app):
    @app.get("/users/{user_id}")
    async def get_user(request):
        return {"user_id": request.path_params["user_id"]}

    route_path, params = app._match_route("/users/123")
    assert route_path == "/users/{user_id}"
    assert params == {"user_id": "123"}


async def test_query_parameters(app):
    @app.get("/search")
    async def search(request):
        return {"query": request.query_params.get("q")}

    request = Request(method="GET", path="/search", headers={}, query_params={"q": "test"}, body=b"")

    route_path, _ = app._match_route("/search")
    handler = app.routes[route_path]["GET"]
    result = await handler(request)

    # Convert dict to Response if needed
    response = result if isinstance(result, Response) else Response(result)

    assert json.loads(response.to_bytes()) == {"query": "test"}
