from miniapi import CORSMiddleware, MiniAPI, Request

app = MiniAPI()
app.add_middleware(CORSMiddleware(allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]))


@app.get("/users")
async def get_users():
    return {"data": [{"name": "Test User"}]}


@app.get("/users/{id}")
async def get_user(request: Request):
    id = request.path_params["id"]
    return {"data": [{"name": "single Test User", "id": id}]}


if __name__ == "__main__":
    app.run()
