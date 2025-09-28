class ConnectionManager:
    def __init__(self):
        self.clients = {}

    async def connect(self, scenario_id: int, token, websocket):
        await websocket.accept(subprotocol=token)
        if not scenario_id in self.clients:
            self.clients[scenario_id] = []
        self.clients[scenario_id].append(websocket)

    async def disconnect(self, scenario_id: int, websocket):
        self.clients[scenario_id].remove(websocket)
        await websocket.close(code=1008)

    def count_connections(self, scenario_id: int):
        return len(self.clients.get(scenario_id, []))
        

    async def send_personal_message(self, data: dict, websocket):
        await websocket.send_json(data)

    async def broadcast(self, scenario_id: int, message: str):
        for connection in self.clients.get(scenario_id, []):
            await connection.send_text(message)

    async def broadcast_json(self, scenario_id: int, data: dict):
        connections = self.clients.get(scenario_id, [])
        for connection in connections[:]: # iterate over a copy
            try:
                await connection.send_json(data)
            except Exception as e:
                connections.remove(connection)

    async def close_all(self, scenario_id: int):
        for connection in self.clients.get(scenario_id, []):
            await connection.close(code=1008)
        self.clients[scenario_id] = []
