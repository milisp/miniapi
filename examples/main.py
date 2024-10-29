# examples/main.py
__author__ = ["ClaudeAI", "milisp"]

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from miniapi3 import CORSMiddleware, MiniAPI, Request, Response, html

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


class UserCreate(BaseModel):
    name: str
    age: int
    email: str


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
async def create_user(request: Request, user: UserCreate, session=Session()):
    try:
        user = User(**user.dict())
        session.add(user)
        session.commit()
        return Response({"message": "User created"}, status=201)
    finally:
        session.close()


@app.put("/users/{user_id}")
async def update_user(request: Request, user_id: int):
    session = Session()
    try:
        data = await request.json()
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return Response({"message": "User not found"}, status=404)

        for key, value in data.items():
            setattr(user, key, value)

        session.commit()
        return {"message": "User updated"}
    finally:
        session.close()


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    session = Session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return Response({"message": "User not found"}, status=404)

        session.delete(user)
        session.commit()
        return {"message": "User deleted"}
    finally:
        session.close()


@app.websocket("/ws")
async def websocket_handler(ws):
    await ws.accept()
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Message text was: {data}")


@app.websocket("/json-chat")
async def json_chat_handler(ws):
    print("start ws")
    await ws.accept()
    while True:
        data = await ws.receive_text()
        print(data)
        await ws.send_text(f"Message text was: {data}")


@app.get("/api")
async def get_user_query(username: str, age: int):
    return {"message": f"Query user {username}", "age": age}


@app.get("/users/search")
async def get_users_by_params(request: Request):
    session = Session()
    try:
        params = request.query_params
        query = session.query(User)

        if "name" in params:
            query = query.filter(User.name == params["name"][0])
        if "age" in params:
            query = query.filter(User.age == int(params["age"][0]))  # Fixed to use age parameter
        if "email" in params:
            query = query.filter(User.email == params["email"][0])

        users = query.all()
        result = [{"id": u.id, "name": u.name, "age": u.age, "email": u.email} for u in users]
        return {"data": result}
    finally:
        session.close()


@app.get("/chat")
async def chat():
    with open("examples/index.html", "r") as f:
        return html(f.read())


if __name__ == "__main__":
    try:
        import uvicorn

        uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
    except KeyboardInterrupt:
        print("Server stopped")
    except Exception:
        app.run()
