import {useState, useEffect} from "react";
import {fetchWithAuth} from "../utils/api";
import './map_list.css';
import {useNavigate} from "react-router-dom";

const MapList = () => {
    const [maps, setMaps] = useState([])
    const navigate = useNavigate()

    useEffect(() => {
        fetchWithAuth(`${process.env.REACT_APP_API_URL}/maps/`)
            .then(data => {
                console.log(data)
                if (data){
                    setMaps(data)
                }
            })
    }, []);

    const handlePreview = (map_id) => {
        const response = fetch(`http://0.0.0.0:8000/maps/${map_id}?t=${new Date().getTime()}`)
        setTimeout(() => {
            document.location.reload();
        }, 500)
    }


    return (
        <>
        <div className="map_list">
            <h2>Maps</h2>
            {maps.map((map) => (
                <div key={map.id} className="map_card">
                    <div className="map_info">
                        <h2>{map.label}</h2>
                        <span>Layout: {map.layout}</span>
                        {map.image ? (
    <img alt="no image" src={`http://0.0.0.0:8000/static/${map.image}`} />
) : (
    <button onClick={() => handlePreview(map.id)}>Preview</button>
)}
                    </div>
                </div>
            ))}
            <button className="add_map_button" onClick={() => navigate('/creator', {replace: true})}>Add new map</button>
        </div>

    </>
    )
}

export default MapList;