import "./MapButton.css"

const MapButton = ({block, updateCode}) => {
    const imsrc = `/${block}.png`
    
    return (
        <div className="map_button">
            <img
                src={imsrc}
                alt={block}
                onClick={() => updateCode(block)}
                className="map_button_image"
            />
        </div>
    );
}

export default MapButton;