from fastapi import Depends, FastAPI
from dependencies import verify_token
from routers import users, roles, bills
from  models.engine.connection import Base, engine
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind= engine)

app = FastAPI(dependencies=[Depends(verify_token)])

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(roles.router)
app.include_router(bills.router)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}

