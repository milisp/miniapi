from pydantic import BaseModel

from miniapi3 import CORSMiddleware, MiniAPI

app = MiniAPI()
app.add_middleware(CORSMiddleware(allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]))
app.debug = True  # Add this line


class UserCreate(BaseModel):
    username: str
    age: int


@app.post("/users")
async def create_user(user: UserCreate):
    return {"message": f"Created user {user.username}", "age": user.age}


@app.get("/users")
async def get_user():
    users = [UserCreate(username="user1", age=18).model_dump(), UserCreate(username="user2", age=19).model_dump()]
    return {"message": users}


@app.put("/users")
async def update_user(user: UserCreate):
    return {"message": f"Updated user {user.username}", "age": user.age}


@app.delete("/users")
async def delete_user(user: UserCreate):
    return {"message": f"Deleted user {user.username}", "age": user.age}


@app.get("/users/{id}")
async def get_user_by_id(id: int):
    return {"message": f"Get user by id {id}"}


@app.get("/api")
async def get_user_query(username: str, age: int):
    return {"message": f"Query user {username}", "age": age}


@app.get("/")
async def index():
    return {"message": "Hello, World!"}


if __name__ == "__main__":
    app.run()
