from fastapi import Header, HTTPException
from pydantic.fields import T
from starlette.requests import Request
import pdb
from config.config import settings


async def get_token_header(request: Request, x_token: str = Header(...)):
    client = request.app.state.redis
    dd = await client.get('x_token')
    # pdb.set_trace()
    #print(dd, settings.x_token, x_token)
    if x_token == settings.x_token or x_token == dd:
        return True
    else:
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def get_query_token(token: str):
    if token != "jessica":
        raise HTTPException(
            status_code=400, detail="No Jessica token provided")
