class ConnectionManager:
    def __init__(self):
        self.clients = {}

    async def connect(self, scenario_id: int, token, websocket):
        await websocket.accept(subprotocol=token)
        if not scenario_id in self.clients:
            self.clients[scenario_id] = []
        self.clients[scenario_id].append(websocket)

    def disconnect(self, scenario_id: int, websocket):
        self.clients[scenario_id].remove(websocket)

    async def send_personal_message(self, message: str, websocket):
        await websocket.send_text(message)

    async def broadcast(self, scenario_id: int, message: str):
        for connection in self.clients.get(scenario_id, []):
            await connection.send_text(message)

