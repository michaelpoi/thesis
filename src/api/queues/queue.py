import asyncio
import base64
import io
import json
import os
from PIL import Image

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

    async def wait_for_image(self, scenario_id=None, pr=False):
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        queue_name = f'offline_queue_{scenario_id}' if scenario_id else 'offline_queue'
        queue_name = queue_name if not pr else f"{queue_name}_pr"
        async with connection:
            channel = await connection.channel()

            queue = await channel.declare_queue(queue_name)

            return await self._consume_image(queue)

    def split_gif(self, scenario_id, gif_bytes):
        frame_path = settings.static_dir / "offline_gifs"


        if not frame_path.exists():
            frame_path.mkdir(parents=True, exist_ok=True)

        decoded_bytes = base64.b64decode(gif_bytes)

        gif = Image.open(io.BytesIO(decoded_bytes))

        frame = 0

        try:
            while True:
                # Save the current frame
                gif.save(frame_path / f"frame_{scenario_id}_{frame}.png")
                frame += 1
                # Move to next frame
                gif.seek(frame)
        except EOFError:
            pass  # End of frames


    async def _consume_image(self, queue):
        async for message in queue:
            async with message.process():
                mtype = message.headers.get("mtype", None)
                if mtype == 'finish':
                    message_body = json.loads(message.body.decode("utf-8"))
                    print(f"Body received: {message_body}")
                    self.split_gif(message_body['scenario_id'], message_body['gif'])
                    return False
                return message.body




queue = Queue()