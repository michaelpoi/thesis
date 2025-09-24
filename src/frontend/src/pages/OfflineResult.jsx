import React, { useEffect, useState } from "react";
import { useParams, useLocation } from "react-router-dom";
import VehicleTimelinePlot from "../components/VehicleTimeLinePlot";

const OfflineResult = () => {
  const {id} = useParams();
  const { state } = useLocation() || {};

  const frames = state?.frames ?? [];
  const map = state?.map ?? null;
  const step = state?.step ?? 0;
  const reason = state?.reason ?? "Unknown";
  const followId = state?.followId ?? 'agent0';

  return(
    <div>
      <h1>Scenario {id} Result For {followId ?? "—"}</h1>
            <p>Terminated at step {frames.length}</p>
            {reason == 'arrive_dest' ? <h2 style={{ color: 'green' }}>Arrived at Destination</h2> : <span> {reason}</span>}
            <p>Reason: {reason}</p>
      
            <VehicleTimelinePlot
              frames={frames}
              map={map}
              metersToUnits={1}
              followId={followId}
            />
      
    </div>
  )
  
};

export default OfflineResult;
