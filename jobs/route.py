import time
from typing import Union
from datetime import datetime
from fastapi import FastAPI, Query, Body, APIRouter
from apscheduler.triggers.cron import CronTrigger
from scripts.logger import logger
from jobs.jobs import Schedule, aps_test1

router = APIRouter()


# 简单定义返回


def resp_ok(*, code=0, msg="ok", data: Union[list, dict, str] = None) -> dict:
    return {"code": code, "msg": msg, "data": data}


def resp_fail(*, code=1, msg="fail", data: Union[list, dict, str] = None):
    return {"code": code, "msg": msg, "data": data}


def cron_task(a1: str) -> None:
    print(a1, time.strftime("'%Y-%m-%d %H:%M:%S'"))


def app_test01(msg: str = "hi"):
    logger.info(f"run with {msg}")


@router.get("/all", tags=["schedule"], summary="获取所有job信息")
async def get_scheduled_syncs():
    """
    获取所有job
    :return:
    """
    schedules = []
    for job in Schedule.get_jobs():
        schedules.append(
            {"job_id": job.id, "func_name": job.func_ref, "func_args": job.args, "cron_model": str(job.trigger),
             "next_run": str(job.next_run_time)}
        )
    return resp_ok(data=schedules)


@router.get("/once", tags=["schedule"], summary="获取指定的job信息")
async def get_target_sync(
        job_id: str = Query("job1", title="任务id")
):
    job = Schedule.get_job(job_id=job_id)

    if not job:
        return resp_fail(msg=f"not found job {job_id}")

    return resp_ok(
        data={"job_id": job.id, "func_name": job.func_ref, "func_args": job.args, "cron_model": str(job.trigger),
              "next_run": str(job.next_run_time)})


# interval 固定间隔时间调度
@router.post("/interval/schedule/", tags=["schedule"], summary="开启定时:间隔时间循环")
async def add_interval_job(seconds: int = Body(120, title="循环间隔时间/秒,默认120s", embed=True),
                           job_id: str = Body(..., title="任务id", embed=True),
                           run_time: int = Body(time.time(), title="第一次运行时间",
                                                description="默认立即执行", embed=True)
                           ):
    res = Schedule.get_job(job_id=job_id)
    if res:
        return resp_fail(msg=f"{job_id} job already exists")
    schedule_job = Schedule.add_job(app_test01,
                                    'interval',
                                    args=(job_id,),
                                    seconds=seconds,  # 循环间隔时间 秒
                                    id=job_id,  # job ID
                                    next_run_time=datetime.fromtimestamp(
                                        run_time)  # 立即执行
                                    )
    return resp_ok(data={"job_id": schedule_job.id})


# date 某个特定时间点只运行一次
@router.post("/date/schedule/", tags=["schedule"], summary="开启定时:固定只运行一次时间")
async def add_date_job(cronname: str, args: tuple,
                       run_time: str = Body(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), title="时间戳", description="固定只运行一次时间", embed=True),
                       job_id: str = Body(..., title="任务id", embed=True),
                       ):
    res = Schedule.get_job(job_id=job_id)
    if res:
        return resp_fail(msg=f"{job_id} job already exists")
    schedule_job = Schedule.add_job(cronname,
                                    'date',
                                    args=args,
                                    run_date=datetime.strptime(
                                        run_time, '%Y-%m-%d %H:%M:%S'),
                                    id=job_id,  # job ID
                                    )
    logger.info("add job {}".format(schedule_job.id))
    return resp_ok(data={"job_id": schedule_job.id})


# cron 更灵活的定时任务 可以使用crontab表达式
@router.post("/cron/schedule/", tags=["schedule"], summary="开启定时:crontab表达式")
async def add_cron_job(
        job_id: str = Body(..., title="任务id", embed=True),
        crontab: str = Body('*/1 * * * *', title="crontab 表达式"),
        run_time: int = Body(time.time(), title="第一次运行时间",
                             description="默认立即执行", embed=True)
):
    res = Schedule.get_job(job_id=job_id)
    if res:
        return resp_fail(msg=f"{job_id} job already exists")
    schedule_job = Schedule.add_job(cron_task,
                                    CronTrigger.from_crontab(crontab),
                                    args=(job_id,),
                                    id=job_id,  # job ID
                                    next_run_time=datetime.fromtimestamp(
                                        run_time)
                                    )

    return resp_ok(data={"job_id": schedule_job.id})


@router.post("/del", tags=["schedule"], summary="移除任务")
async def remove_schedule(
        job_id: str = Body(..., title="任务id", embed=True)
):
    res = Schedule.get_job(job_id=job_id)
    if not res:
        return resp_fail(msg=f"not found job {job_id}")
    Schedule.remove_job(job_id)
    logger.info("remove job with id={}".format(job_id))
    return resp_ok()
