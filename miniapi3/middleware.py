from .http import Request, Response


class CORSMiddleware:
    def __init__(
        self,
        allow_origins: list[str] = None,
        allow_methods: list[str] = None,
        allow_headers: list[str] = None,
    ):
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or [
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "OPTIONS",
        ]
        self.allow_headers = allow_headers or [
            "Content-Type",
            "Accept",
            "Authorization",
        ]

    def process_response(self, response: Response, request: Request) -> Response:
        # 设置基本的 CORS 头
        headers = {
            "Access-Control-Allow-Origin": ", ".join(self.allow_origins),
            "Access-Control-Allow-Methods": ", ".join(self.allow_methods),
            "Access-Control-Allow-Headers": ", ".join(self.allow_headers),
        }

        # 更新响应头
        response.headers.update(headers)
        return response
