# uvicorn main:app --host=127.0.0.1 --port=8000 --reload
from config.config import settings
from fastapi import Depends, FastAPI, BackgroundTasks, Request
from dependencies import get_token_header
from ops.common import route as common_route
from ops.deploy import route as deploy_route
from ops.wjtx import route as wjtx_route
from jobs import route as jobs_route
from typing import Optional
from scripts.common.redis import get_redis_pool
import pdb
from scripts.logger import logger
from fastapi.middleware.cors import CORSMiddleware

# from apscheduler.events import EVENT_JOB_EXECUTED
# from jobs.jobs import Schedule, job_execute
tags_metadata = [
    # {
    #     "name": "common",
    #     "description": "Operations with users. The **login** logic is also here.",
    # },
    {
        "name": "common",
        "description": "Manage items. So _fancy_ they have their own docs.",
        "externalDocs": {
            "description": "Items external docs",
            "url": "https://fastapi.tiangolo.com/",
        },
    },
]


def create_app():
    application = FastAPI(dependencies=[Depends(get_token_header)],
                          openapi_tags=tags_metadata)
    application.include_router(common_route.router, prefix="/common")
    application.include_router(deploy_route.router, prefix="/deploy")
    application.include_router(wjtx_route.router, prefix="/wjtx")
    # application.include_router(jobs_route.router, prefix="/jobs")
    return application


app = create_app()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    app.state.redis = await get_redis_pool()
    # Schedule.start()
    # Schedule.add_listener(job_execute, EVENT_JOB_EXECUTED)


@app.on_event("shutdown")
async def shutdown_event():
    app.state.redis.close()
    await app.state.redis.wait_close()


@app.get("/")
async def root(request: Request):
    redis_client = request.app.state.redis
    keys = await redis_client.get("online_devices")
    logger.info("get keys was {0} with {1}".format(keys, request.url))
    if keys:
        return {"message": "Hello Bigger Applications! {}".format(keys)}
    else:
        return {"message": "kajsk"}


def write_log(message: str) -> True:
    with open("log.txt", mode="a") as log:
        log.write(message)
    return True


def get_query(background_tasks: BackgroundTasks, q: Optional[str] = None):
    if q:
        message = f"found query:{q}\n"
        background_tasks.add_task(write_log, message)
    return q


@app.post("/send-notification/{email}")
async def send_notification(request: Request, email: str, background_tasks: BackgroundTasks, q: str = Depends(get_query)):
    redis_client = request.app.state.redis
    keys = await redis_client.get("online_devices")
    logger.info("get keys = {}".format(keys))
    message = f"message to {email} \n"
    background_tasks.add_task(write_log, message)
    return {"message": "Message sent"}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app='main:app', host="127.0.0.1",
                port=8010, reload=True, debug=True)
