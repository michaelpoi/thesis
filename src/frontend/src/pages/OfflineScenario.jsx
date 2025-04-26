import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import './Offline.css';

const OfflineScenario = () => {
    const [scenarioImgSrc, setScenarioImgSrc] = useState(null);
    const [previewImgSrc, setPreviewImgSrc] = useState(null);
    const [moves, setMoves] = useState([
        { steps: 1, steering: 0, acceleration: 0 }
    ]);

    const [newMove, setNewMove] = useState({ steps: "", steering: "", acceleration: "" });

    const { id, vehicle_id } = useParams();

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
            steering: Number(newMove.steering),
            acceleration: Number(newMove.acceleration)
        }]);
        setNewMove({ steps: "", steering: "", acceleration: "" });
    };

    const handlePreview = async () =>{
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

        const response = await fetch(`${process.env.REACT_APP_API_URL}/offline/submit/`, {
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
                <span>Steering: {newMove.steering}</span>
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
                />
                <span>Acceleration: {newMove.acceleration}</span>
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
                />
                <button type="submit">Add Move</button>
            </form>
        </div>
    );
};

export default OfflineScenario;
