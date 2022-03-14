import datetime
from scripts.logger import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from scripts.logger import logger
import json


Schedule = AsyncIOScheduler(
    jobstores={
        'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
    },
    executors={
        'default': ThreadPoolExecutor(20),
        'processpool': ProcessPoolExecutor(5)
    }, job_defaults={
        'coalesce': False,
        'max_instances': 3
    }
)


def job_execute(event):
    """
    监听事件处理
    :param event:
    :return:
    """
    logger.info(
        "job执行job:\ncode => {}\njob.id => {}\njobstore=>{}".format(
            event.code,
            event.job_id,
            event.jobstore
        ))


def aps_test1(x):
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), json.dumps(x))
    logger.info("run appt_test1,msg={}".format(json.dumps(x)))


def app_test01(msg: str = "hi"):
    logger.info(f"run with {msg}")
