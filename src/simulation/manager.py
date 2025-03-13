import json

from worker import Worker
import aio_pika
from schemas import InitEnv
import asyncio
from multiprocessing import Process
from utils import get_rabbitmq_url

class Manager:
    def __init__(self, rabbitmq_url:str, init_queue:str):
        self.workers = set()
        self.rabbitmq_url = rabbitmq_url
        self.init_queue = init_queue

    async def setup(self):
        pass

    async def serve(self):
        connection = await aio_pika.connect(url=self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(self.init_queue, durable=True)
            async for message in queue:
                async with message.process():
                    body = json.loads(message.body)
                    await self.add_process(body)


    async def handle_preview(self, scenario):
        worker = Worker(scenario)
        process = Process(target=worker.map_preview)
        process.start()
        process.join()
        return

    async def add_process(self, body):
        scenario = InitEnv(**body)
        if not scenario.map.image:
            return await self.handle_preview(scenario)
        if scenario.id not in self.workers:
            worker = Worker(scenario)
            process = Process(target=worker.work)
            process.start()
            self.workers.add(scenario.id)
        else:
            pass

if __name__ == "__main__":
    manager = Manager(get_rabbitmq_url(), "init_queue")
    asyncio.run(manager.serve())