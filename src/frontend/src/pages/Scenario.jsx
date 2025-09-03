import React, { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import mpld3 from "mpld3";

const Scenario = () => {
  const location = useLocation();
  const navigate = useNavigate()
  const { task, usedVehicle } = location.state || {};
  const ws = useRef(null); // Use useRef for WebSocket
  // const [imageSrc, setImageSrc] = useState(null);
  const [plot, setPlot] = useState(null);

  console.log(usedVehicle)


  const handleKeyDown = (e) => {
    switch (e.which) {
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
    const socket = new WebSocket(`ws://127.0.0.1/api/tasks/ws/${task.id}/${usedVehicle}/`, [localStorage.getItem('token')]);

    ws.current = socket; // Store socket in ref

    socket.onmessage = (event) => {
      try {

        // const blob = new Blob([event.data], { type: "image/png" });
        // const url = URL.createObjectURL(blob); // Create an object URL
        // setImageSrc(url); // Set image source
        console.log(event.data);
        const data = JSON.parse(event.data); // Parse JSON
        setPlot(data);
      } catch (error) {
        console.error("Error processing WebSocket message:", error);
      }

      socket.onerror = () => {
        navigate('/', { replace: true })
      }

      socket.onclose = (event) => {
        console.log(`websocket closed code: ${event.code}`)
        navigate('/', { replace: true })
        switch (event.code) {
          case 1000:
            navigate(`/result/${task.id}/`, { replace: true });
            break;
          case 4001:
            navigate(`/login`, { replace: true });
            break;
          case 1008:
            navigate(`/result/${task.id}/`, { replace: true });
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

  useEffect(() => {
    if (plot) {
      const figDiv = document.getElementById("fig1");
      if (figDiv){
        figDiv.innerHTML = ""; // Clear previous plot
      }
      mpld3.draw_figure("fig1", plot);
    }
  }, [plot]);

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
        {/* {plot ? (
          <iframe
            srcDoc={plot}
            title="mpld3 plot"
            style={{ width: "100%", height: "500px", border: "none" }}
          />
        ) : (
          <p>Waiting for plot...</p>
        )} */}

        <div id="fig1"></div>


      </div>
    </div>
  );
};

export default Scenario;
