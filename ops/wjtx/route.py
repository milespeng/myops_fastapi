from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form
from starlette.requests import Request
from starlette.responses import JSONResponse
from config.config import settings
from scripts.wjtx.tools import WjtxTools
from uuid import uuid4
router = APIRouter()


@router.post("/change_starttime", tags=["wjtx"], summary="修改服务器启动时间")
async def change_starttime(request: Request, serverid: int, starttime: str) -> JSONResponse:
    wj = WjtxTools()
    await wj.change_start_time(serverid, starttime)
    return JSONResponse(status_code=200, content={"message": "restart server {0},starttime={1}!".format(serverid, starttime)})


@router.post("/change_worldboss", tags=["wjtx"], summary="修改世界boss血量配置")
async def change_worldboss(request: Request, serverid: int, values: int) -> JSONResponse:
    wj = WjtxTools()
    await wj.change_worldboss(serverid, values)
    return JSONResponse(status_code=200, content={"message": "change  {0} worldboss to {1}!".format(serverid, values)})


@router.get("/stop_serivce", tags=["wjtx"], summary="stop wjtx service")
async def stop_service(request: Request, serverid: int) -> JSONResponse:
    wj = WjtxTools()
    await wj.stop_service(serverid)
    return JSONResponse(status_code=200, content={"message": "stop  {0} services!".format(serverid)})
