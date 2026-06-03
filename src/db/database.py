import os
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(os.getenv("DATABASE_URI"))
collection = client[os.getenv("DATABASE_NAME")]