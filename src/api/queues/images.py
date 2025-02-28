import aio_pika
import io
from settings import settings

class ImageQueue:
    def __init__(self, rabbitmq_url:str):
        self.rabbitmq_url = rabbitmq_url

    async def consume_results(self):
        print("Got Image")
        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue('image_queue', durable=True)

            async for message in queue:
                async with message.process():
                    io_bytes = io.BytesIO(message.body)

                    with open('/app/output.png', 'wb+') as f:
                        f.write(io_bytes.getvalue())


queue = ImageQueue(rabbitmq_url=settings.rabbitmq_url)

