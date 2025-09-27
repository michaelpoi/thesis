import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import "./Offline.css";
import StaticVehiclePlot from "../components/StaticVehiclePlot";
import Speedometer from "../components/Speedometer";
import VehicleTimelinePlot from "../components/VehicleTimeLinePlot";

const OfflineScenario = () => {
    const [vehicles, setVehicles] = useState([]);
    const [previewVehicles, setPreviewVehicles] = useState([]);
    const [map, setMap] = useState(null);
    const [step, setStep] = useState(0);
    const [egoAgentID, setEgoAgentID] = useState("");
    const [moves, setMoves] = useState([{ steps: 1, steering: 0, acceleration: 0 }]);
    const [currentSpeed, setCurrentSpeed] = useState(0);
    const [frames, setFrames] = useState([]);
    const [previewFrames, setPreviewFrames] = useState([]);
    const [frameStartInd, setFrameStartInd] = useState(0);
    const [startInd, setStartInd] = useState(0);
    const [fps, setFps] = useState(20);
    const [fpsMultiplyer, setFpsMultiplyer] = useState(1);
    const framesRef = useRef([]);

    const egoAgentIDRef = useRef(egoAgentID);
    const pingTurnRef = useRef(0);

    const [pingActive, setPingActive] = useState(false);
    const pingActiveRef = useRef(false);

    const setPing = (val) => {
        pingActiveRef.current = val;
        setPingActive(val);
    };

    const [newMove, setNewMove] = useState({ steps: 100, steering: "", acceleration: "" });
    const navigate = useNavigate();
    const { id, vehicle_id } = useParams();

    const goResult = () => {
    navigate(`/offline_result/${id}/`, {
      replace: true,
      state: {
        reason: "Unknown",
        frames: framesRef.current,
        map: map,
        step: step,
        followId: egoAgentIDRef.current || 'agent0',
      },
    });
  };

    const setMoveByAlias = (alias) => {
        switch (alias) {
            case "UP":
                setNewMove((prev) => ({ ...prev, acceleration: 0.3, steering: 0.0 }));
                break;
            case "DOWN":
                setNewMove((prev) => ({ ...prev, acceleration: -0.3, steering: 0.0 }));
                break;
            case "LEFT":
                setNewMove((prev) => ({ ...prev, acceleration: 0.0, steering: -0.3 }));
                break;
            case "RIGHT":
                setNewMove((prev) => ({ ...prev, acceleration: 0.0, steering: 0.3 }));
                break;
            default:
                break;
        }
    };

    useEffect(() => {
        fetch(`${process.env.REACT_APP_API_URL}/offline/init/${id}/`, { method: "POST" });
    }, [id]);

    const handleChange = (e) => {
        setNewMove({ ...newMove, [e.target.name]: e.target.value });
    };

    const handleFrameStartChange = (e) => {
        e.preventDefault();
        setFrameStartInd(frames.length - startInd);
        setFps(20 * fpsMultiplyer);
    };

    const handleStartInd = (e) => {
        setStartInd(e.target.value);
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        setMoves([
            ...moves,
            {
                steps: Number(newMove.steps),
                steering: Number(-newMove.steering),
                acceleration: Number(newMove.acceleration),
            },
        ]);
        setNewMove({ steps: "", steering: "", acceleration: "" });
    };

    const handlePreview = async () => {
        const response = await fetch(`${process.env.REACT_APP_API_URL}/offline/preview/`, {
            method: "POST",
            body: JSON.stringify({
                scenario_id: Number(id),
                vehicle_id: Number(vehicle_id),
                moves: moves,
            }),
            headers: { "Content-Type": "application/json" },
        });

        const raw = await response.json();
        const plt = raw.plt ?? raw;

        if (raw.frames) {
            setPreviewFrames((prev) => [...prev, ...raw.frames]);
        }

        if (plt?.positions) {
            const nextVehicles = Object.entries(plt.positions).map(([id, agent]) => ({
                id,
                pos: agent.position,
                heading: agent.heading ?? 0,
                color: id == egoAgentIDRef.current ? 0xff3b30 : 0x2ecc71,
            }));
            setPreviewVehicles(nextVehicles);
        }
    };

    const handleMove = async () => {
        const response = await fetch(`${process.env.REACT_APP_API_URL}/offline/submit/`, {
            method: "POST",
            body: JSON.stringify({
                scenario_id: Number(id),
                vehicle_id: Number(vehicle_id),
                moves: moves,
            }),
            headers: { "Content-Type": "application/json" },
        });

        if (response.status === 405) {
            navigate(`/offline_result/${id}/`, { replace: true });
            return;
        }

        const raw = await response.json();

        // If empty {} -> start ping
        if (Object.keys(raw).length === 0) {
            setPing(true);
            pollPing(); // kick off
            return;
        }

        pingTurnRef.current = raw.turn;

        applyResult(raw.data, raw.tm);
        setMoves(raw.next?.moves || []);
    };

    /** Apply server result (either submit or ping) */
    const applyResult = (raw, tm) => {
        const plt = raw.plt ?? raw;

        if (plt?.positions) {
            const nextVehicles = Object.entries(plt.positions).map(([id, agent]) => ({
                id,
                pos: agent.position,
                heading: agent.heading ?? 0,
                color: id == egoAgentIDRef.current ? 0xff3b30 : 0x2ecc71,
            }));
            setVehicles(nextVehicles);

            if (egoAgentIDRef.current) {
                const velocityVector = plt.positions[egoAgentIDRef.current]?.velocity || [0, 0];
                const v = Math.hypot(velocityVector[0], velocityVector[1]) * 3.6;
                setCurrentSpeed(v);
            }
        }

        if (raw.frames) {
            setFrames((prev) => [...prev, ...raw.frames]);
            framesRef.current = [...framesRef.current, ...raw.frames];
        }

        if (!raw.alive){
            goResult();
            return
        }

        if(tm){
            goResult();
            return
        }

        if (plt?.map && Object.keys(plt.map).length) {
            setMap((prev) => prev || plt.map);
        }
        if (raw.step != null) setStep(raw.step);

        if (!egoAgentID && raw.agents_map != null) {
            const agentId = raw.agents_map[vehicle_id];
            console.log(agentId);
            egoAgentIDRef.current = agentId;
            setEgoAgentID(agentId);
        }
    };

    /** Ping loop */
    const pollPing = async () => {
        if (!pingActiveRef.current) return;
        try {
            const res = await fetch(
                `${process.env.REACT_APP_API_URL}/offline/ping/${id}/${vehicle_id}/${pingTurnRef.current + 1}/`
            );

            if (res.status === 200) {
                const raw = await res.json();
                setMoves(raw.next?.moves || []);
                applyResult(raw.data, raw.tm);

                // got a real result -> stop pinging
                pingTurnRef.current = raw.turn
                setPing(false);
                return;
            }
        } catch (err) {
            console.error("Ping error:", err);
        }

        // retry later
        if (pingActiveRef.current) {
            setTimeout(pollPing, 1000);
        }
    };

    return (
        <div>
            <h1>Main Scenario</h1>
            <div className="image-container">
                {pingActive ? <img src="/loading.gif" alt="" /> : <VehicleTimelinePlot
                    frames={frames}
                    map={map}
                    metersToUnits={1}
                    followId={egoAgentIDRef.current}
                    fps={fps}
                    loop={true}
                    startPaused={false}
                    startIndex={frameStartInd}
                />}



                <h1>Preview Scenario</h1>
                <VehicleTimelinePlot
                    frames={previewFrames}
                    map={map}
                    metersToUnits={1}
                    followId={egoAgentIDRef.current}
                    fps={20}
                    loop={true}
                    startPaused={false}
                />

                <form onSubmit={handleFrameStartChange}>
                    <input
                        type="number"
                        name="start_ind"
                        placeholder="Number of frames to show"
                        value={startInd}
                        onChange={handleStartInd}
                    />
                    
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <button
                            type="button"
                            style={{ backgroundColor: fpsMultiplyer === 0.5 ? "blue" : "grey" }}
                            onClick={() => setFpsMultiplyer(0.5)}
                        >
                            0.5x
                        </button>
                        <button
                            type="button"
                            style={{ backgroundColor: fpsMultiplyer === 1 ? "blue" : "grey" }}
                            onClick={() => setFpsMultiplyer(1)}
                        >
                            1x
                        </button>
                        <button
                            type="button"
                            style={{ backgroundColor: fpsMultiplyer === 2 ? "blue" : "grey" }}
                            onClick={() => setFpsMultiplyer(2)}
                        >
                            2x
                        </button>
                    </div>

                    <button type="submit">Apply</button>
                </form>
            </div>
            <div style={{display: "flex", justifyContent: "center"}}>
                <button onClick={handlePreview} disabled={pingActive}>Preview</button>
                <button onClick={handleMove} disabled={pingActive}>Submit</button>
            </div>
            

            <h2>Moves List</h2>
            <div className="moves-list">
                {moves.map((move, index) => (
                    <div key={index} className="move-card">
                        <p>
                            <strong>Move {index + 1}</strong>
                        </p>
                        <p>Steps: {move.steps}</p>
                        <p>Steering: {move.steering}</p>
                        <p>Acceleration: {move.acceleration}</p>
                        <button
                            onClick={() => {
                                const newMoves = moves.filter((_, i) => i !== index);
                                setMoves(newMoves);
                            }}
                        >
                            Remove
                        </button>
                    </div>
                ))}
            </div>
            {!pingActive && <>
                <h3>Add New Move</h3>
                <form onSubmit={handleSubmit}>
                    <input
                        type="number"
                        name="steps"
                        placeholder="Steps"
                        value={newMove.steps}
                        onChange={handleChange}
                        required
                    />
                    <div style={{ marginBottom: "1rem" }}>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                            <span>LEFT</span>
                            <span>Steering: {-newMove.steering}</span>
                            <span>RIGHT</span>
                        </div>
                        <input
                            type="range"
                            min={-1}
                            max={1}
                            step={0.1}
                            name="steering"
                            value={newMove.steering}
                            onChange={handleChange}
                            required
                            style={{ width: "100%" }}
                        />
                    </div>

                    <div>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                            <span>BRAKE</span>
                            <span>Acceleration: {newMove.acceleration}</span>
                            <span>ACCELERATE</span>
                        </div>
                        <input
                            type="range"
                            min={-1}
                            max={1}
                            step={0.1}
                            name="acceleration"
                            value={newMove.acceleration}
                            onChange={handleChange}
                            required
                            style={{ width: "100%" }}
                        />
                    </div>
                    <div className="arrow-keypad">
                        <div className="empty"></div>
                        <button type="button" onClick={() => setMoveByAlias("UP")}>
                            ↑
                        </button>
                        <div className="empty"></div>
                        <button type="button" onClick={() => setMoveByAlias("LEFT")}>
                            ←
                        </button>
                        <button type="button" onClick={() => setMoveByAlias("DOWN")}>
                            ↓
                        </button>
                        <button type="button" onClick={() => setMoveByAlias("RIGHT")}>
                            →
                        </button>
                    </div>
                    <div className="add-move-wrapper">
                        <button type="submit">Add Move</button>
                    </div>
                </form>
            </>}

        </div>
    );
};

export default OfflineScenario;
