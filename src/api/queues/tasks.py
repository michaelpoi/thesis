import json

from settings import settings
from schemas.results import Scenario, Move
import aio_pika

class TaskQueue:
    def __init__(self, rabbitmq_url:str, task_queue:str, result_queue:str, envs_queue:str):
        self.rabbitmq_url = rabbitmq_url
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.envs_queue = envs_queue

    async def send_task(self, task, type:str):
        move_data = {
            "type": type,
            "data": task.model_dump()
        }
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                message=aio_pika.Message(body=json.dumps(move_data).encode()),
                routing_key=self.task_queue,
            )

    async def init_scenario(self, scenario:Scenario):
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        body = {
            "type": "CREATE ENV",
            "data": scenario.model_dump()
        }
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                message=aio_pika.Message(body=json.dumps(body).encode()),
                routing_key=self.envs_queue,
            )


    async def consume_results(self, callback: callable):
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(self.result_queue, durable=True)

            async for message in queue:
                async with message.process():
                    result = Scenario.model_validate_json(message.body)
                    callback(result)


queue = TaskQueue(rabbitmq_url=settings.rabbitmq_url,
                  task_queue=settings.task_queue,
                  result_queue=settings.result_queue,
                  envs_queue="envs_queue",)


