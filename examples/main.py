# examples/main.py
__author__ = ["ClaudeAI", "milisp"]

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from miniapi import CORSMiddleware, MiniAPI, Request, Response

app = MiniAPI()
app.add_middleware(CORSMiddleware(allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]))

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    email = Column(String)


engine = create_engine("sqlite:///db.sqlite")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


@app.get("/")
async def index():
    return "Hello World!"


@app.get("/users")
async def get_users(request: Request):
    session = Session()
    try:
        users = session.query(User).all()
        result = [{"id": u.id, "name": u.name, "age": u.age, "email": u.email} for u in users]
        return {"data": result}
    finally:
        session.close()


@app.post("/users")
async def create_user(request: Request, session=Session()):
    data = await request.json()
    try:
        user = User(**data)
        session.add(user)
        session.commit()
        return Response({"message": "User created"}, status=201)
    finally:
        session.close()


@app.get("/users/{user_id}")
async def get_user(request):
    user_id = request.path_params["user_id"]
    return {"user_id": user_id}


@app.put("/users/{user_id}")
async def update_user(request):
    user_id = request.path_params["user_id"]
    return {"user_id": user_id}


@app.delete("/users/{user_id}")
async def delete_user(request):
    user_id = request.path_params["user_id"]
    return Response({"message": f"User deleted {user_id}"}, status=204)


@app.websocket("/ws")
async def websocket_handler(ws):
    while True:
        message = await ws.receive()
        await ws.send(f"Echo: {message}")


if __name__ == "__main__":
    try:
        import uvicorn

        uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
    except KeyboardInterrupt:
        print("Server stopped")
    except Exception:
        app.run()
