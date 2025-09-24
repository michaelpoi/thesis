import {useState, useEffect} from "react";
import {fetchWithAuth} from "../utils/api";
import './map_list.css';
import {useNavigate} from "react-router-dom";
import Header from "../components/Header";

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



    return (
        <>
            <Header></Header>
        <div className="map_list">
            <h2>Maps</h2>
            {maps.map((map) => (
                <div key={map.id} className="map_card">
                    <div className="map_info">
                        <h2>{map.label}</h2>
                        <span>Layout: {map.layout}</span>
                        
                    </div>
                </div>
            ))}
            <button className="add_map_button" onClick={() => navigate('/creator', {replace: true})}>Add new map</button>
        </div>

    </>
    )
}

export default MapList;