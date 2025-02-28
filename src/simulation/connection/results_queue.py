import json
import os
import io

import aio_pika
from schemas import ScenarioStep, Move, InitEnv
from core.env_manager import env_manager
from core.move_converter import MoveConverter
from metadrive.envs import MetaDriveEnv
from PIL import Image

class ResultsQueue:
    def __init__(self, rabbitmq_url:str, task_queue:str, result_queue:str):
        self.rabbitmq_url = rabbitmq_url
        self.task_queue = task_queue
        self.result_queue = result_queue

    async def send_result(self, task:ScenarioStep):
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                message=aio_pika.Message(body=task.json().encode()),
                routing_key=self.result_queue,
            )

    async def send_picture(self, image_bytes):
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                message = aio_pika.Message(image_bytes),
                routing_key='image_queue',
            )

    async def consume_results(self, queue=None):
        if not queue:
            queue = self.task_queue
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(queue, durable=True)

            async for message in queue:
                async with message.process():
                    body = json.loads(message.body)
                    print(body)
                    await self.task_distributor(body["type"], body["data"])


    async def task_distributor(self, type, data):
        if type == "CREATE ENV":
            scenario = InitEnv(**data)
            await self.add_env(scenario)
            print(env_manager.envs)
        elif type == "MOVE":
            move = Move(**data)
            await self.move(move)



    async def move(self, step:Move):
        print(env_manager.envs)
        env = env_manager.get_env(step.scenario_id)

        # config = {
        #     "use_render": False,
        #     "traffic_density": 0.1,
        # }
        # env = MetaDriveEnv(config=config)
        # env.reset()
        move_arr = MoveConverter.convert(step)
        res = env.step(move_arr)
        vehicle_position = env.vehicle.position
        print(vehicle_position)
        image = env.render(mode='topdown',
                           window=False)

        bytes_io = io.BytesIO()

        img = Image.fromarray(image)

        print(img)

        img.save(bytes_io, format="PNG")

        image_bytes = bytes_io.getvalue()

        await self.send_picture(image_bytes)




    async def add_env(self,scenario):
        print(f"Received AddEnv scenario {scenario}")
        env_manager.add_env(scenario.id)

def get_rabbitmq_url():

    url = "amqp://{}:{}@{}/".format(
                                     os.getenv('rq_user', 'guest'),
                                     os.getenv('rq_password', 'guest'),
                                     os.getenv('rq_host'))

    print(url)
    return url

results_queue = ResultsQueue(rabbitmq_url=get_rabbitmq_url(),
                             task_queue='task_queue',
                             result_queue='result_queue')


