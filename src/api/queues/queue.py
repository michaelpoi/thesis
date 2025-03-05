import json

from schemas.results import Move, Scenario
from settings import settings
import aio_pika

class Queue:
    def __init__(self):
        self.rabbitmq_url = settings.rabbitmq_url

    def get_queue_name(self, scenario_id):
        return f"moves_{scenario_id}"

    async def send_move(self, move: Move):
        move_json = json.dumps(move.model_dump())
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                message=aio_pika.Message(body=move_json.encode()),
                routing_key=self.get_queue_name(move.scenario_id),
            )

    async def send_init(self, scenario: Scenario):
        scenario_json = json.dumps(scenario.model_dump())
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                message=aio_pika.Message(body=scenario_json.encode()),
                routing_key="init_queue",
            )

queue = Queue()