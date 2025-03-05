import asyncio
import base64
import io
import json
from time import sleep
from metadrive.envs import MetaDriveEnv
from schemas import Move
from core.move_converter import MoveConverter
from PIL import Image
import aio_pika
from utils import get_rabbitmq_url
import logging


class Worker:
    def __init__(self, scenario):
        self.rabbitmq_url = get_rabbitmq_url()
        self.scenario = scenario
        self.env = None

    @property
    def move_queue_name(self):
        return f"moves_{self.scenario.id}"

    @property
    def results_queue_name(self):
        return f"images_queue"

    def setup_env(self):
        config = {
            "use_render": False,
            "traffic_density": 0.1,
        }
        self.env = MetaDriveEnv(config=config)
        self.env.reset()

    async def send_frame(self, image_bytes):
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()

            message_body = {
                "scenario_id": self.scenario.id,
                "image_bytes": base64.b64encode(image_bytes).decode("utf-8")  # Convert bytes to base64 string
            }

            message_data = json.dumps(message_body).encode("utf-8")

            await channel.default_exchange.publish(
                aio_pika.Message(body=message_data),
                routing_key=self.results_queue_name,
            )

    async def process_move(self, move: Move):
        move_arr = MoveConverter.convert(move)
        self.env.step(move_arr)
        image = self.env.render(mode='topdown', window=False)

        bytes_io = io.BytesIO()
        img = Image.fromarray(image)
        img.save(bytes_io, format="PNG")
        image_bytes = bytes_io.getvalue()

        await self.send_frame(image_bytes)

    async def consume_moves(self):
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(self.move_queue_name, durable=True)

            async for message in queue:
                async with message.process():
                    move_json = json.loads(message.body)
                    move = Move(**move_json)
                    await self.process_move(move)

    async def run(self):
        self.setup_env()
        await self.consume_moves()

    def work(self):
        logging.warn(f"Starting worker process {self.scenario.id}")
        asyncio.run(self.run())


