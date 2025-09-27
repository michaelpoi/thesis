import React, { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import VehiclePlot from "../components/VehiclePlot";
import Speedometer from "../components/Speedometer";

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
  const [egoAgentID, setEgoAgentID] = useState("");

  // ---- keep latest values in refs so handlers can read them ----
  const vehiclesRef = useRef(vehicles);
  const mapRef = useRef(map);
  const stepRef = useRef(step);
  const reasonRef = useRef(reason);
  const egoAgentIDRef = useRef(egoAgentID);
  const [currentSpeed, setCurrentSpeed] = useState(0);
  const [sensAcceleration, setSensAcceleration] = useState(0.3);
  const [sensSteering, setSensSteering] = useState(0.15);

  const sensAccelerationRef = useRef(0.3);
  const sensSteeringRef = useRef(0.15);

  const setAcc = (e) => {
    const val = parseFloat(e.target.value)
    setSensAcceleration(val);
    sensAccelerationRef.current = val;
  }

  const setStr = (e) =>{
    const val = parseFloat(e.target.value)
    setSensSteering(val);
    sensSteeringRef.current = val;
  }

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
      ws.current.send(JSON.stringify({ direction, timestamp: Date.now(), sens_acceleration: sensAccelerationRef.current, sens_steering: sensSteeringRef.current }));
    }
  };

  const goResult = () => {
    navigate(`/result/${task.id}/`, {
      replace: true,
      state: {
        reason: (reasonRef.current) || "Unknown",
        vehicles: vehiclesRef.current,
        map: mapRef.current,
        step: stepRef.current,
        followId: egoAgentIDRef.current || 'agent0',
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

        console.log(raw.agents_map)


        if (raw.alive === false) {
          reasonRef.current = raw.reason || "Unknown";
          setReason(raw.reason || "Unknown");
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
            goal: agent?.goal ?? null,
            color: id == egoAgentIDRef.current ? 0xff3b30 : 0x2ecc71,
          }));

          vehiclesRef.current = nextVehicles;
          setVehicles(nextVehicles);
          if (egoAgentIDRef.current) {
            const velocityVector = plt.positions[egoAgentIDRef.current]?.velocity || [0, 0];
            const v = Math.hypot(velocityVector[0], velocityVector[1]) * 3.6; // m/s to km/h
            setCurrentSpeed(v);
          };


        }

        // Map once
        if (plt?.map && Object.keys(plt.map).length) {
          mapRef.current = plt.map;
          setMap((prev) => prev || plt.map);
        }

        if (raw.time) setPing(Date.now() - raw.time);
        stepRef.current = raw.step ?? stepRef.current;
        if (raw.step != null) setStep(raw.step);
        if (!egoAgentID && raw.agents_map != null) {
          const agentId = raw.agents_map[usedVehicle];
          egoAgentIDRef.current = agentId;
          setEgoAgentID(agentId);
        }
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
        {/* <button onClick={() => sendDirection("UP")}>Up</button>
        <button onClick={() => sendDirection("DOWN")}>Down</button>
        <button onClick={() => sendDirection("LEFT")}>Left</button>
        <button onClick={() => sendDirection("RIGHT")}>Right</button> */}

        <div style={{ margin: "14px 0" }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <label>Acceleration sensitivity</label>
            <span>{sensAcceleration.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min={0.1}
            max={1}
            step={0.05}
            value={sensAcceleration}
            onChange={(e) => setAcc(e)}
            style={{ width: "100%" }}
          />
        </div>
        <div style={{ margin: "14px 0" }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <label>Steering sensitivity</label>
            <span>{sensSteering.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min={0.1}
            max={1}
            step={0.05}
            value={sensSteering}
            onChange={(e) => setStr(e)}
            style={{ width: "100%" }}
          />
        </div>
      </div>
      <h4>Current ping: {ping}</h4>
      <h4>Current step: {step}</h4>

      <div style={{ display: "flex", justifyContent: "center", margin: "20px 0" }}>
        <Speedometer speed={currentSpeed} max={200} units="km/h" />
      </div>

      <VehiclePlot
        vehicles={vehicles}
        map={map}
        metersToUnits={1}
        followId={egoAgentIDRef.current || 'agent0'}
      />
    </div>
  );
};

export default Scenario;
