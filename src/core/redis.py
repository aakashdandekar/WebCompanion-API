import os
from fastapi import Request
from redis.asyncio import Redis

redis = Redis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    db=0,
    username=os.getenv("REDIS_USERNAME"),
    password=os.getenv("REDIS_PASSWORD")
)

def getRedis(request: Request):
    return request.app.state.redis