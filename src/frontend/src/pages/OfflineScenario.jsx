import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import './Offline.css';

const OfflineScenario = () => {
    const [scenarioImgSrc, setScenarioImgSrc] = useState(null);
    const [previewImgSrc, setPreviewImgSrc] = useState(null);
    const [moves, setMoves] = useState([
        { steps: 1, steering: 0, acceleration: 0 }
    ]);

    const [newMove, setNewMove] = useState({ steps: 100, steering: "", acceleration: "" });
    const navigate = useNavigate()

    const { id, vehicle_id } = useParams();

    const setMoveByAlias = (alias) => {
        switch (alias) {
            case "UP":
                setNewMove(prev => ({ ...prev, acceleration: 0.3, steering: 0.0 }));
                break;
            case "DOWN":
                setNewMove(prev => ({ ...prev, acceleration: -0.3, steering: 0.0 }));
                break;
            case "LEFT":
                setNewMove(prev => ({ ...prev, acceleration: 0.0, steering: -0.3 }));
                break;
            case "RIGHT":
                setNewMove(prev => ({ ...prev, acceleration: 0.0, steering: 0.3 }));
                break;
        }
    };


    useEffect(() => {
        fetch(`${process.env.REACT_APP_API_URL}/offline/init/${id}/`, {
            method: "POST"
        });
    }, [id]);

    const handleChange = (e) => {
        setNewMove({ ...newMove, [e.target.name]: e.target.value });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        setMoves([...moves, {
            steps: Number(newMove.steps),
            steering: Number(-newMove.steering),
            acceleration: Number(newMove.acceleration)
        }]);
        setNewMove({ steps: "", steering: "", acceleration: "" });
    };

    const handlePreview = async () =>{

        setPreviewImgSrc('/loading.gif')
        const body = JSON.stringify({
                scenario_id: Number(id),
                moves: moves
            })

        console.log(body)
        const response = await fetch(`${process.env.REACT_APP_API_URL}/offline/preview/`, {
            method: "POST",
            body: JSON.stringify({
                scenario_id: Number(id),
                vehicle_id: Number(vehicle_id),
                moves: moves
            }),
            headers: { "Content-Type": "application/json" },
        });

        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        setPreviewImgSrc(imageUrl); // Update the preview image source
    };

    const handleMove = async () =>{

        setScenarioImgSrc('/loading.gif')

        const response = await fetch(`${process.env.REACT_APP_API_URL}/offline/submit/`, {
            method: "POST",
            body: JSON.stringify({
                scenario_id: Number(id),
                vehicle_id: Number(vehicle_id),
                moves: moves
            }),
            headers: { "Content-Type": "application/json" },
        });

        if (response.status === 405){
            navigate(`/offline_result/${id}/`, {replace: true});
        }

        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        setScenarioImgSrc(imageUrl); // Update the preview image source

        setMoves([]);
    };

    return (
        <div>
            <div className="image-container">
                <h1>Main Scenario</h1>
                {scenarioImgSrc && <img src={scenarioImgSrc} alt="No scenario" className="main-scenario"/>}
            <h1>Preview Scenario</h1>
            {previewImgSrc && <img src={previewImgSrc} alt="No scenario" className="preview-scenario"/>}
            </div>
            <button onClick={handlePreview}>Preview</button>
            <button onClick={handleMove}>Submit</button>
            <h2>Moves List</h2>
            <div className="moves-list">
                {moves.map((move, index) => (
                    <div key={index} className="move-card">
                        <p><strong>Move {index + 1}</strong></p>
                        <p>Steps: {move.steps}</p>
                        <p>Steering: {move.steering}</p>
                        <p>Acceleration: {move.acceleration}</p>
                        <button onClick={() => {
                            const newMoves = moves.filter((_, i) => i !== index);
                            setMoves(newMoves);
                        }}>
                            Remove
                        </button>
                    </div>
                ))}
            </div>

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
                <div style={{ marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
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
                        placeholder="Steering"
                        value={newMove.steering}
                        onChange={handleChange}
                        required
                        style={{ width: '100%' }}
                    />
                </div>

                <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
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
                        placeholder="Acceleration"
                        value={newMove.acceleration}
                        onChange={handleChange}
                        required
                        style={{ width: '100%' }}
                    />
                </div>

                <div className="arrow-keypad">
                    <div className="empty"></div>
                    <button onClick={() => setMoveByAlias("UP")}>↑</button>
                    <div className="empty"></div>

                    <button onClick={() => setMoveByAlias("LEFT")}>←</button>
                    <button onClick={() => setMoveByAlias("DOWN")}>↓</button>
                    <button onClick={() => setMoveByAlias("RIGHT")}>→</button>
                </div>


                <div className="add-move-wrapper">
                  <button type="submit">Add Move</button>
                </div>
            </form>
        </div>
    );
};

export default OfflineScenario;
