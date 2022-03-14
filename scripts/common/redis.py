from aioredis import create_redis_pool, Redis
from config.config import settings

# settings = {
#     "redis_host": "192.168.100.30",
#     "redis_port": 6379,
#     "redis_db": 1,

# }


async def get_redis_pool() -> Redis:
    redis = await create_redis_pool("redis://{ip}:{port}/{db}?encoding=utf-8".format(ip=settings.redis_host, port=settings.redis_port, db=settings.redis_db))
    return redis
