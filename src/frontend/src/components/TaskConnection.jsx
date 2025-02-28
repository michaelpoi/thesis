import React, { useEffect, useRef, useState } from "react";

const TaskConnection = ({ task, usedVehicle }) => {
  const [messages, setMessages] = useState([]);
  const ws = useRef(null); // Use useRef for WebSocket

  const handleKeyDown = (e) => {
    switch (e.which){
      case 87:
        sendDirection("UP")
        break;
      case 68:
        sendDirection("RIGHT")
        break;
      case 65:
        sendDirection("LEFT")
        break;
      case 83:
        sendDirection("DOWN")
        break;
    }
  };

  const sendDirection = (direction) => {
    if (ws.current) {
      console.log(direction);
      ws.current.send(direction);
    }
  };

  useEffect(() => {
    // Create WebSocket connection
    const socket = new WebSocket(`ws://localhost:8000/tasks/ws/${task.id}/${usedVehicle}/`);

    ws.current = socket; // Store socket in ref

    socket.onmessage = (event) => {
      setMessages((prev) => [...prev, event.data]);
    };

    // Add keydown event listener
    document.addEventListener("keydown", handleKeyDown);

    // Cleanup event listener and WebSocket connection on unmount
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      socket.close();
    };
  }, [task.id, usedVehicle]); // Reconnect WebSocket when task or vehicle changes

  return (
    <div>
      <h3>Connected to Task: {task.name}</h3>
      <div>
        <button onClick={() => sendDirection("UP")}>Up</button>
        <button onClick={() => sendDirection("DOWN")}>Down</button>
        <button onClick={() => sendDirection("LEFT")}>Left</button>
        <button onClick={() => sendDirection("RIGHT")}>Right</button>
      </div>
      <div>
        <h4>Messages:</h4>
        <ul>
          {messages.map((msg, index) => (
            <li key={index}>{msg}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default TaskConnection;
