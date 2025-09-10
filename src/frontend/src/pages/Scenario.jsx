import React, { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import VehiclePlot from "../components/VehiclePlot";

const Scenario = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { task, usedVehicle } = location.state || {};
  const ws = useRef(null);

  const [vehicles, setVehicles] = useState([]);
  const [map, setMap] = useState(null);   // 👈 store the map here (once)
  const [ping, setPing] = useState(0);
  const [step, setStep] = useState(0);

  const handleKeyDown = (e) => {
    switch (e.which) {
      case 87: sendDirection("UP"); break;
      case 68: sendDirection("RIGHT"); break;
      case 65: sendDirection("LEFT"); break;
      case 83: sendDirection("DOWN"); break;
      default: break;
    }
  };

  const sendDirection = (direction) => {
    if (ws.current) {
      ws.current.send(JSON.stringify({ direction, timestamp: Date.now() }));
    }
  };

  useEffect(() => {
    const socket = new WebSocket(
      `ws://127.0.0.1/api/tasks/ws/${task.id}/${usedVehicle}/`,
      [localStorage.getItem("token")]
    );
    ws.current = socket;

    socket.onmessage = (event) => {
      try {
        const raw = JSON.parse(event.data);
        const alive = raw.alive
        console.log(alive)
        const plt = raw.plt ?? raw; // your payload uses { plt: { positions, map }, time }

        // Vehicles from positions:
        if (plt?.positions) {
          const nextVehicles = Object.entries(plt.positions).map(([id, agent]) => ({
            id,
            pos: agent.position,
            heading: agent.heading, // keep simple; or compute from velocity if you want
            color: agent.is_human ? 0xff3b30 : 0x2ecc71,
          }));
          setVehicles(nextVehicles);
        }

        // Map only once (first time it appears)
        if (plt?.map && Object.keys(plt.map).length) {
          setMap((prev) => (prev ? prev : plt.map));
        }

        if (raw.time) setPing(Date.now() - raw.time);
        setStep(raw.step);
      } catch (err) {
        console.error("WS parse error:", err);
      }
    };

    socket.onerror = () => navigate("/", { replace: true });

    socket.onclose = (event) => {
      switch (event.code) {
        case 1000: navigate(`/result/${task.id}/`, { replace: true }); break;
        case 4001: navigate(`/login`, { replace: true }); break;
        case 1008: navigate(`/result/${task.id}/`, { replace: true }); break;
        default:  navigate("/", { replace: true });
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      socket.close();
    };
  }, [task.id, usedVehicle, navigate]);

  return (
    <div>
      <h3>Connected to Task: {task.name}</h3>
      <div>
        <button onClick={() => sendDirection("UP")}>Up</button>
        <button onClick={() => sendDirection("DOWN")}>Down</button>
        <button onClick={() => sendDirection("LEFT")}>Left</button>
        <button onClick={() => sendDirection("RIGHT")}>Right</button>
      </div>
      <h4>Current ping: {ping}</h4>
      <h4>Current step: {step}</h4>

      <VehiclePlot
        vehicles={vehicles}
        map={map}                 // 👈 pass the map here
        metersToUnits={1}
        followId="agent0"
      />
    </div>
  );
};

export default Scenario;
