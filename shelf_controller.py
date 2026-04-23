import asyncio
import websockets


class ShelfController:
    def __init__(self, ip="172.20.10.11", port=81):
        self.uri = f"ws://{ip}:{port}"
        self.ws = None
        self.status = [True] * 10

    async def connect(self):
        self.ws = await websockets.connect(self.uri)
        asyncio.create_task(self._listen())

    async def _listen(self):
        while True:
            try:
                msg = await self.ws.recv()
                if msg.startswith("STATUS "):
                    bits = msg[7:]
                    self.status = [b == "1" for b in bits]
            except:
                break

    async def release(self, slot):
        await self.ws.send(f"release {slot}")

    async def hold(self, slot):
        await self.ws.send(f"hold {slot}")

    async def release_all(self):
        await self.ws.send("release_all")

    async def hold_all(self):
        await self.ws.send("hold_all")

    async def get_status(self):
        await self.ws.send("status")
        await asyncio.sleep(0.1)
        return self.status

    async def disconnect(self):
        if self.ws:
            await self.ws.close()
