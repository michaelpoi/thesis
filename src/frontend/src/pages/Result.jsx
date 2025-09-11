import React from "react";
import { useLocation, useParams, useNavigate } from "react-router-dom";
import VehiclePlot from "../components/VehiclePlot";

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

  return (
    <div>
      <h1>Scenario {id} Result For {followId ?? "—"}</h1>
      <p>Terminated at step {step}</p>
      <p>Reason: {reason}</p>

      <VehiclePlot
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
