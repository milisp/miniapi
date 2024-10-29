import asyncio


class Server:
    @staticmethod
    async def run_server(app, host: str, port: int):
        server = await asyncio.start_server(app.handle_request, host, port)
        print(f"Server running on http://{host}:{port}")
        async with server:
            await server.serve_forever()
