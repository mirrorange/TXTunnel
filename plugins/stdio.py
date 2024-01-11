import sys
import asyncio
from . import IOPlugin


class StdIO(IOPlugin):
    async def get(self) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sys.stdin.readline)

    async def put(self, data: str):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, sys.stdout.write, data)
        sys.stdout.flush()

    async def start(self):
        pass

    async def stop(self):
        pass


PLUGIN = StdIO
