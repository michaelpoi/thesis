import React, { useEffect, useState } from "react";

const TaskConnection = ({ task, usedVehicle}) => {
  const [messages, setMessages] = useState([]);
  const [ws, setWs] = useState(null);

  const handleKeyDown = (e) => {
    console.log(e.which);
    if (e.which === 87) {
      sendDirection("UP");
    }
  };

  const sendDirection = (direction) => {
    if (ws) {
      console.log(direction);
      ws.send(direction);
    }
  };

  useEffect(() => {
    // Create WebSocket connection
    
    const socket = new WebSocket(`ws://localhost:8000/tasks/ws/${task.id}/${usedVehicle}/`);
    
    setWs(socket);

    socket.onmessage = (event) => {
      setMessages((prev) => [...prev, event.data]);
    };
    // socket.onerror = (error) => {
    //   alert("Not able to connect");
    //   socket.close()
    // };

    // Add keydown event listener when the component mounts
    document.addEventListener("keydown", handleKeyDown);

    // Clean up the event listener and WebSocket connection when the component unmounts
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      // disconnect();
      socket.close();
      
    };
  }, [task.id]);
  ;

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
