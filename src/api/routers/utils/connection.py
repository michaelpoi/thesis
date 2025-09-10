class ConnectionManager:
    def __init__(self):
        self.clients = {}

    async def connect(self, scenario_id: int, token, websocket):
        await websocket.accept(subprotocol=token)
        if not scenario_id in self.clients:
            self.clients[scenario_id] = []
        self.clients[scenario_id].append(websocket)

    async def disconnect(self, scenario_id: int, websocket):
        await websocket.close(code=1008)
        self.clients[scenario_id].remove(websocket)

    async def send_personal_message(self, data: dict, websocket):
        await websocket.send_json(data)

    async def broadcast(self, scenario_id: int, message: str):
        for connection in self.clients.get(scenario_id, []):
            await connection.send_text(message)

    async def broadcast_json(self, scenario_id: int, data: dict):
        for connection in self.clients.get(scenario_id, []):
            await connection.send_json(data)

    async def close_all(self, scenario_id: int):
        for connection in self.clients.get(scenario_id, []):
            await connection.close()
        self.clients[scenario_id] = []
