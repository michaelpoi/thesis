import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

const OfflineResult = () => {
  const { id } = useParams();
  const [frames, setFrames] = useState([]);
  const [currentFrame, setCurrentFrame] = useState(0);

  useEffect(() => {
    const loadFrames = async () => {
      const loadedFrames = [];
      let frameIndex = 0;
      let found = true;

      while (found) {
        const frameUrl = `${process.env.REACT_APP_API_URL}/static/offline_gifs/frame_${id}_${frameIndex}.png`;

        try {
          const response = await fetch(frameUrl, { method: "HEAD" }); // HEAD request to check if file exists
          if (response.ok) {
            loadedFrames.push(frameUrl);
            frameIndex++;
          } else {
            found = false; // 404 or not ok -> stop loading
          }
        } catch (error) {
          found = false; // Network error -> stop loading
        }
      }

      setFrames(loadedFrames);
    };

    loadFrames();
  }, [id]);

  const handlePrev = () => {
    setCurrentFrame((prev) => (prev === 0 ? frames.length - 1 : prev - 1));
  };

  const handleNext = () => {
    setCurrentFrame((prev) => (prev + 1) % frames.length);
  };

  return (
    <div className="offline_result_container">
      <h3 className="offline_result_title">Offline Task Result</h3>

      <div className="offline_result_card">
        <div className="offline_result_info">
          {frames.length > 0 ? (
            <>
              <img
                src={frames[currentFrame]}
                alt={`Frame ${currentFrame}`}
                className="offline_result_image"
              />
              <div className="offline_result_controls">
                <button onClick={handlePrev} className="offline_result_button">Previous</button>
                <button onClick={handleNext} className="offline_result_button">Next</button>
              </div>
              <div className="offline_result_counter">
                Frame {currentFrame + 1} / {frames.length}
              </div>
            </>
          ) : (
            <p>Loading frames...</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default OfflineResult;
