import React, { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import VehiclePlot from "../components/VehiclePlot";

const Scenario = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { task, usedVehicle } = location.state || {};
  const ws = useRef(null);

  const [vehicles, setVehicles] = useState([]);
  const [map, setMap] = useState(null);
  const [ping, setPing] = useState(0);
  const [step, setStep] = useState(0);
  const [reason, setReason] = useState("");

  // ---- keep latest values in refs so handlers can read them ----
  const vehiclesRef = useRef(vehicles);
  const mapRef = useRef(map);
  const stepRef = useRef(step);
  const reasonRef = useRef(reason);

  // useEffect(() => { vehiclesRef.current = vehicles; }, [vehicles]);
  // useEffect(() => { mapRef.current = map; }, [map]);
  // useEffect(() => { stepRef.current = step; }, [step]);
  // useEffect(() => { reasonRef.current = reason; }, [reason]);

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

  const goResult = () => {
    navigate(`/result/${task.id}/`, {
      replace: true,
      state: {
        reason: (reasonRef.current) || "Unknown",
        vehicles:  vehiclesRef.current,
        map: mapRef.current,
        step: stepRef.current,
        followId: `agent${usedVehicle - 1}`,
      },
    });
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
        const plt = raw.plt ?? raw;


        if (raw.alive === false) {
          reasonRef.current = plt.reason || "Unknown";
          setReason(plt.reason || "Unknown");
          goResult();
          socket.close(1000, "Scenario ended");
          return;
        }

        // Update vehicles
        if (plt?.positions) {
          const nextVehicles = Object.entries(plt.positions).map(([id, agent]) => ({
            id,
            pos: agent.position,
            heading: agent.heading ?? 0,
            color: agent.is_human ? 0xff3b30 : 0x2ecc71,
          }));
          vehiclesRef.current = nextVehicles;
          setVehicles(nextVehicles);
        }

        // Map once
        if (plt?.map && Object.keys(plt.map).length) {
          mapRef.current = plt.map;
          setMap((prev) => prev || plt.map);
        }

        if (raw.time) setPing(Date.now() - raw.time);
        stepRef.current = raw.step ?? stepRef.current;
        if (raw.step != null) setStep(raw.step);

        // If scenario ended, navigate using the freshest data.
        
      } catch (err) {
        console.error("WS parse error:", err);
      }
    };

    socket.onerror = () => navigate("/", { replace: true });

    socket.onclose = (event) => {
      // Use the last known snapshot from refs
      switch (event.code) {
        case 4001:
          navigate(`/login`, { replace: true });
          break;
        case 1008:
          goResult();
          break;
        case 1000:
          goResult();
          break;
        default:
          goResult();
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
        map={map}
        metersToUnits={1}
        followId={`agent0`}
      />
    </div>
  );
};

export default Scenario;
