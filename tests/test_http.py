from miniapi3 import Request, Response


async def test_request_json():
    request = Request(
        method="POST",
        path="/test",
        headers={"Content-Type": "application/json"},
        query_params={},
        body=b'{"key": "value"}',
    )

    data = await request.json()
    assert data == {"key": "value"}


def test_response_creation():
    # Test JSON response
    json_response = Response({"message": "success"})
    assert json_response.content_type == "application/json"
    assert json_response.status == 200

    # Test HTML response
    html_response = Response("<!DOCTYPE html><html></html>")
    assert html_response.content_type == "text/html"

    # Test custom status
    error_response = Response({"error": "not found"}, status=404)
    assert error_response.status == 404
