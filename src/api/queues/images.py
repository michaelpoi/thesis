import base64
import json
import os

import aio_pika
import io
from settings import settings
from db.scenario_repository import ScenarioRepository
from database import async_session
from models.scenario import ScenarioStatus
import aio_pika.exceptions

class ImageQueue:
    def __init__(self, rabbitmq_url:str):
        self.rabbitmq_url = rabbitmq_url

    # def save_frame(self, scenario_id, step_num, image_bytes):
    #     #file_name = settings.static_dir / "frames" / str(scenario_id) / f"{str(step_num)}.png"
    #     file_name = settings.base_dir / f"{scenario_id}.png"
    #     dir_name = os.path.dirname(file_name)
    #
    #     if not os.path.exists(dir_name):
    #         os.makedirs(dir_name, exist_ok=True)
    #
    #     decoded_bytes = base64.b64decode(image_bytes)
    #
    #     with open(file_name, "wb+") as f:
    #         f.write(decoded_bytes)

    def save_gif(self, scenario_id, gif_bytes):
        gif_path = settings.static_dir / "gifs" / f"{scenario_id}.gif"

        dir_name = os.path.dirname(gif_path)

        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        decoded_bytes = base64.b64decode(gif_bytes)

        with open(gif_path, "wb+") as f:
            f.write(decoded_bytes)

    async def consume_results(self, scenario_id: int):
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue('images_queue', durable=True)

            last_relevant_message = None

            while True:
                try:
                    message = await queue.get(timeout=0.1, no_ack=False)
                except aio_pika.exceptions.QueueEmpty:
                    break  # No more messages to check

                async with message.process():
                    try:
                        message_body = json.loads(message.body.decode("utf-8"))
                    except Exception:
                        continue  # Skip if message is malformed

                    if message_body['scenario_id'] != scenario_id:
                        continue  # Skip other scenarios

                    status = message_body.get('status')

                    if status == 'FINISHED':
                        async with async_session() as session:
                            scenario = await ScenarioRepository.get_scenario(session, scenario_id)
                            scenario.status = ScenarioStatus.FINISHED
                            await session.commit()

                        return {
                            'alive': False,
                            'gif': base64.b64decode(message_body['gif'])
                        }

                    elif status == 'ACTIVE':
                        # Save the latest relevant frame
                        last_relevant_message = message_body

            # After consuming all messages, return the last relevant frame
            if last_relevant_message:
                return {
                    'alive': True,
                    'image': base64.b64decode(last_relevant_message['image_bytes'])
                }

            # No relevant message found
            return None


queue = ImageQueue(rabbitmq_url=settings.rabbitmq_url)

