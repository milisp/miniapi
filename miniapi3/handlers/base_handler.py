from urllib.parse import parse_qs


class BaseHandler:
    @staticmethod
    def parse_headers(scope):
        return {k.decode(): v.decode() for k, v in scope["headers"]}

    @staticmethod
    def parse_query(scope):
        query_params = {}
        raw_query = scope.get("query_string", b"").decode()
        if raw_query:
            query_dict = parse_qs(raw_query)
            query_params = {
                k: [v.decode() if isinstance(v, bytes) else v for v in vals] for k, vals in query_dict.items()
            }
        return query_params
