import React from "react";
import { useLocation, useParams, useNavigate } from "react-router-dom";
import StaticVehiclePlot from "../components/StaticVehiclePlot";

const Result = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { state } = useLocation() || {};
  console.log("Result state:", state);

  const vehicles = state?.vehicles ?? [];
  const map = state?.map ?? null;
  const step = state?.step ?? 0;
  const reason = state?.reason ?? "Unknown";
  const followId = state?.followId ?? (vehicles[0]?.id || null);

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

  return (
    <div>
      <h1>Scenario {id} Result For {followId ?? "—"}</h1>
      <p>Terminated at step {step}</p>
      <h2 style={getReasonStyle(reason)}>{getReasonText(reason)}</h2>

      <StaticVehiclePlot
        vehicles={vehicles}
        map={map}
        metersToUnits={1}
        followId={followId}
      />

      <button onClick={() => navigate(-1)}>Back</button>
    </div>
  );
};

export default Result;
