import {useEffect, useState} from "react";
import MapButton from "../components/MapButton";
import './MapCreator.css';
import {fetchWithAuth} from "../utils/api";
import {useNavigate} from "react-router-dom";
import Header from "../components/Header";

const MapCreator = () =>{
    const [code, setCode] = useState('');
    const [mapId, setMapId] = useState(null);
    const [imageSrc, setImageSrc] = useState(null);
    const [label, setLabel] = useState(null)
    const navigate = useNavigate();

    useEffect(() => {
        if (!mapId) return
        setImageSrc('/loading.gif')
        const interval = setInterval(() => {
            setImageSrc(`${process.env.REACT_APP_API_URL}/static/${mapId}.png?t=${Date.now()}`);
        }, 2000); // Check every 3 seconds

        return () => clearInterval(interval);
    }, [mapId]);

    const handleManualCodeInsertion = (e) =>{
        setCode(e.target.value);
    }

    const updateMap = (block) => {
        setCode(prev => (prev + block))
    }
    const handleAddMap = () => {
        fetchWithAuth(`${process.env.REACT_APP_API_URL}/maps/`,
            {
                method: "POST",
                body: JSON.stringify({layout: code, label: label})
            }).then(data => {
                setMapId(data.id)
        })



    }

    const handleUpdate = () => {
        const response = fetch(`${process.env.REACT_APP_API_URL}/maps/${mapId}?t=${Date.now()}`,
            {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({layout: code})
            }
            )

        // setTimeout(() => {
        //     document.location.reload();
        // }, 500)
    }

    const blocks = ["S", "r", "O", "y", "$", "T", "C", "R", "X", "Y"]

    return (
        <>
            <Header></Header>
            <div className="map_add">
            <h2>Map Creator</h2>
            {mapId && <h3>Map: {label}</h3>}
            {!mapId &&
                <input
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                className="map_input"
                placeholder="Enter map label..."
            />
            }

            <input
                value={code}
                onChange={handleManualCodeInsertion}
                className="map_input"
                placeholder="Enter map code..."
            />
            {mapId && (
                <img src={imageSrc} alt="Map preview" className="map_preview"/>
            )}
            <div className="buttons_menu">
                {blocks.map((block, index) => (
                    <MapButton key={index} block={block} updateCode={updateMap} />
                ))}
            </div>
            {mapId &&
                <>
                    <button className="preview_map_button" onClick={handleUpdate}>
                        Update
                    </button>
                    <button className="add_map_button" onClick={() => navigate('/maps', {replace:true})}>
                        Done
                    </button>
                </>

            }

            {!mapId &&
                    <button className="add_map_button" onClick={handleAddMap}>
                        Add Map
                    </button>
            }

        </div>
        </>
    );
}

export default MapCreator;