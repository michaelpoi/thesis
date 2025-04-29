import json

from worker import Worker
import aio_pika
from schemas import InitEnv
import asyncio
from multiprocessing import Process
from utils import get_rabbitmq_url
from offline_worker import OfflineWorker

class Manager:
    def __init__(self, rabbitmq_url:str, init_queue:str):
        self.workers = set()
        self.offline_workers = set()
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
                    mtype = message.headers.get('mtype')
                    body = json.loads(message.body)
                    await self.add_process(body, mtype)


    async def handle_preview(self, scenario):
        worker = Worker(scenario)
        process = Process(target=worker.map_preview)
        process.start()
        process.join()
        return

    async def add_process(self, body, mtype):
        scenario = InitEnv(**body)
        if mtype == 'rl':
            if scenario.id in self.workers:
                return
            worker_class = Worker
            self.workers.add(scenario.id)
        elif mtype == 'map':
            await self.handle_preview(scenario)
            return
        else:
            if scenario.id in self.offline_workers:
                return
            worker_class = OfflineWorker
            self.offline_workers.add(scenario.id)

        if not scenario.map.image:
            await self.handle_preview(scenario)

        worker = worker_class(scenario)
        process = Process(target=worker.work)
        process.start()


if __name__ == "__main__":
    manager = Manager(get_rabbitmq_url(), "init_queue")
    asyncio.run(manager.serve())