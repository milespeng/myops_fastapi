# pip install fastapi-mail
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form
from starlette.requests import Request
from starlette.responses import JSONResponse
from config.config import settings
from scripts.common.deploy import ProjectInfo, deploy_service, ClientAliyun, sync_aliyun
from uuid import uuid4
router = APIRouter()


@router.post("/server", tags=["deploy"], summary="部署服务器端")
async def deploy_server(project: ProjectInfo, tag: str,
                        background_tasks: BackgroundTasks) -> JSONResponse:
    uuid = uuid4().hex
    background_tasks.add_task(deploy_service, project, tag, uuid)
    return JSONResponse(status_code=200,
                        content={
                            "message":
                            "{0} {1} deploy success,uuid={2}!".format(
                                project.name, tag, uuid)
                        })


@router.post("/sync_aliyun", tags=["deploy"], summary="发布到阿里云CDN")
async def sync_aliyun(clientinfo: ClientAliyun,
                      background_tasks: BackgroundTasks) -> JSONResponse:
    background_tasks.add_task(sync_aliyun, clientinfo)
    return JSONResponse(status_code=200,
                        content={
                            "message":
                            "{0} rsync aliyun CDN success!".format(clientinfo)
                        })
