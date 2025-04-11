import asyncio
import json

from schemas.results import Move, Scenario
from settings import settings
import aio_pika

from schemas.offline import OfflineScenarioPreview


class Queue:
    def __init__(self):
        self.rabbitmq_url = settings.rabbitmq_url

    def get_queue_name(self, scenario_id):
        return f"moves_{scenario_id}"

    def get_offline_queue_name(self, scenario_id):
        return f"offline_{scenario_id}"

    async def send_message(self, queue_name, body, headers=None):
        if not headers:
            headers = {}
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                message=aio_pika.Message(body=body.encode(), headers=headers),
                routing_key=queue_name,
            )

    async def send_move(self, move: Move):
        move_json = json.dumps(move.model_dump())
        await self.send_message(self.get_queue_name(move.scenario_id),
                                move_json)

    async def send_offline_sequence(self, moves, scenario_id):
        move_json = json.dumps(moves)
        headers = {"mtype": "main"}
        await self.send_message(self.get_offline_queue_name(scenario_id), move_json,
                                headers=headers)


    async def send_offline_move(self, move: OfflineScenarioPreview, is_preview=False):
        if is_preview:
            move_json = json.dumps(move.model_dump())
        else:
            move_json = json.dumps(move)
        headers = {"mtype": "preview"} if is_preview else {"mtype": "main"}
        await self.send_message(self.get_offline_queue_name(move.scenario_id), move_json,
                                headers=headers)

    async def send_init(self, scenario, mtype='rl'):
        scenario_json = json.dumps(scenario.model_dump())
        await self.send_message("init_queue", scenario_json, {"mtype": mtype} )

    async def wait_for_image(self):
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()

            # ✅ Correct queue name
            queue = await channel.declare_queue('offline_queue')

            try:
                return await asyncio.wait_for(self._consume_image(queue), timeout=10)  # ⏳ 10 sec timeout
            except asyncio.TimeoutError:
                print("⏳ Timeout waiting for image.")
                return None

    async def _consume_image(self, queue):
        async for message in queue:
            async with message.process():
                return message.body




queue = Queue()