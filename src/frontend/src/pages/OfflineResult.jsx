import React, { useEffect, useState } from "react";
import { useParams, useLocation } from "react-router-dom";
import VehicleTimelinePlot from "../components/VehicleTimeLinePlot";

const OfflineResult = () => {
  const {id} = useParams();
  const { state } = useLocation() || {};

  const frames = state?.frames ?? [];
  const map = state?.map ?? null;
  const reason = state?.reason ?? "Unknown";
  const followId = state?.followId ?? 'agent0';

  const getReasonText = (reason) => {
    switch (reason) {
      case 'crash_vehicle':
        return 'Crashed into another vehicle';
      case 'out_of_road':
        return 'Went out of the road';
      case 'arrive_dest':
        return 'Arrived at destination';
      case 'max_step':
        return 'Reached maximum steps';
      default:
        return 'Unknown reason';
    }
  };

  const getReasonStyle = (reason) => {
    if (reason === 'arrive_dest') {
      return { color: 'green' };
    }

    return { color: 'red' };
  }

  return(
    <div>
      <h1>Scenario {id} Result For {followId ?? "—"}</h1>
            <p>Terminated at step {frames.length}</p>
            <h2 style={getReasonStyle(reason)}>{getReasonText(reason)}</h2>
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
