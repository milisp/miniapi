import pytest

from miniapi3.router import Router


@pytest.fixture
def router():
    return Router()


def test_router_registration(router):
    @router.get("/test")
    async def handler(request):
        return {"message": "test"}

    assert "/test" in router.routes
    assert "GET" in router.routes["/test"]


def test_router_pattern_matching(router):
    @router.get("/users/{user_id}/posts/{post_id}")
    async def handler(request):
        pass

    route_path, params = router._match_route("/users/123/posts/456")
    assert route_path == "/users/{user_id}/posts/{post_id}"
    assert params == {"user_id": "123", "post_id": "456"}


def test_router_no_match(router):
    route_path, params = router._match_route("/nonexistent")
    assert route_path is None
    assert params is None
