from connection.results_queue import results_queue
import asyncio


async def main():
    await results_queue.consume_results()

if __name__ == '__main__':
    asyncio.run(main())
