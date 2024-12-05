import os

import motor.motor_asyncio

from dotenv import load_dotenv

load_dotenv('.env')

class MongoDB:
    def __init__(self):
        self.mongo_uri = os.getenv('MONGO_URL')
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.mongo_uri)
        self.db_name = 'test'
        self.db = self.client[self.db_name]

    async def close(self):
        self.client.close()

mongo_db = MongoDB()