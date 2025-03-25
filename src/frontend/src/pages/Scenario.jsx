import React, { useEffect, useRef, useState } from "react";
import {useLocation, useNavigate} from "react-router-dom";

const Scenario = () => {
  const location = useLocation();
  const navigate = useNavigate()
  const {task, usedVehicle} = location.state || {};
  const ws = useRef(null); // Use useRef for WebSocket
  const [imageSrc, setImageSrc] = useState(null);
  const [currentStep, setCurrentStep]= useState(0);


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
    const socket = new WebSocket(`ws://localhost:8000/tasks/ws/${task.id}/${usedVehicle}/`, [localStorage.getItem('token')]);

    ws.current = socket; // Store socket in ref

    socket.onmessage = (event) => {
    try {
      // The message is already a string, parse it directly
      const data = JSON.parse(event.data);

      // setCurrentStep(data.step); // Update the step state

      // Convert base64 string to Blob
      const byteCharacters = atob(data.image);
      const byteNumbers = new Array(byteCharacters.length)
        .fill(0)
        .map((_, i) => byteCharacters.charCodeAt(i));
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: "image/png" });

      const url = URL.createObjectURL(blob); // Create an object URL
      setImageSrc(url); // Set image source
    } catch (error) {
      console.error("Error processing WebSocket message:", error);
    }

    socket.onerror = () => {
      navigate('/', {replace: true})
    }

    socket.onclose = (event) => {
      console.log(`websocket closed code: ${event.code}`)
      switch (event.code){
        case 1000:
          navigate(`/result/${task.id}/`, {replace: true});
          break;
        case 4001:
          navigate(`/login`, {replace: true});
          break;
        case 1008:
          navigate(`/result/${task.id}/`, {replace: true});
          break;
      }
    }
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
        <h4>Step {currentStep} / {task.steps}</h4>
        <h4>Messages:</h4>
              {imageSrc ? <img src={imageSrc} alt="WebSocket Image" /> : <p>Waiting for image...</p>}
      </div>
    </div>
  );
};

export default Scenario;
