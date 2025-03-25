import React, { useEffect, useRef, useState } from "react";
import {useLocation, useNavigate, useParams} from "react-router-dom";

const Result = () => {

    const {id} = useParams();

  return (
    <div>
      <h3>Task Result</h3>

      <div>

        <h4>Messages:</h4>
              <img src={`${process.env.REACT_APP_API_URL}/static/gifs/${id}.gif`} alt="Scenario GIF" />
      </div>
    </div>
  );
};

export default Result;
