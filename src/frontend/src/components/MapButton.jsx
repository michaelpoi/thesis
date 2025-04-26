import "./MapButton.css"

const MapButton = ({block, updateCode}) => {

    let imsrc;

    if (block === 'R'){
        imsrc = `/r1.png`
    }
    else{
        if (block === 'Y'){
            imsrc = '/y1.png'
        }
        else{
            imsrc = `/${block}.png`
        }
    }
    
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