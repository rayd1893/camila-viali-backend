import os
from dotenv import load_dotenv
from fastapi import Header, HTTPException
from typing import Annotated

load_dotenv()

async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != os.getenv("SECRET_TOKEN"):
        raise HTTPException(status_code=400, detail="X-Token header invalid")
