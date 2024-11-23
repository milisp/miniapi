from miniapi3 import CORSMiddleware, Request, Response


def test_cors_middleware():
    middleware = CORSMiddleware()
    kwargs = dict(
        allow_origins=["http://localhost:3000"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    request = Request(method="GET", path="/test", headers={}, query_params={}, body=b"")

    response = Response({"message": "test"})
    processed_response = middleware.process_response(response, request, kwargs)

    assert processed_response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
    assert processed_response.headers["Access-Control-Allow-Methods"] == "GET, POST"
    assert processed_response.headers["Access-Control-Allow-Headers"] == "Content-Type"
