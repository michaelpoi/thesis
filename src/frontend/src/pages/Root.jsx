import React, { useState, useEffect, useCallback } from "react";
import "../components/task_list.css";
import { useNavigate } from "react-router-dom";
import { fetchWithAuth } from "../utils/api";


const Root = () => {
  const [tasks, setTasks] = useState([]);
  const navigate = useNavigate();

  // load my tasks
  useEffect(() => {
    let ignore = false;

    (async () => {
      try {
        const data = await fetchWithAuth(`${process.env.REACT_APP_API_URL}/tasks/mine/`);
        if (!ignore && Array.isArray(data)) setTasks(data);
      } catch (err) {
        console.error("Failed to fetch tasks:", err);
      }
    })();

    return () => { ignore = true; };
  }, []);

  const getUserId = useCallback(async () => {
    const data = await fetchWithAuth(`${process.env.REACT_APP_API_URL}/auth/user/`);
    return data?.id;
  }, []);

  const onConnect = useCallback((task, vid) => {
    navigate(`/scenario/${task.id}`, { state: { 'task': task,'usedVehicle':vid } });
  }, [navigate]);

  const onOffline = useCallback((task, vid) => {
    navigate(`/offline/${task.id}/${vid}`);
  }, [navigate]);

  const onProceed = useCallback(async (task) => {
    try {
      const uid = await getUserId();
      if (!uid) {
        console.warn("No user id found");
        return;
      }

      const vehicle = (task.vehicles || []).find(v => v.assigned_user_id === uid);
      const vid = vehicle?.id;

      console.log(vid)

      if (!vid) {
        console.warn("No assigned vehicle for this user in the task.");
        return;
      }

      if (task.is_offline) {
        onOffline(task, vid);
      } else {
        onConnect(task, vid);
      }
    } catch (err) {
      console.error("Failed to proceed:", err);
    }
  }, [getUserId, onConnect, onOffline]);

  return (
    <div className="scenario_list">
      {tasks.map((task) => (
        <div
          key={task.id}
          className="scenario_card"
          style={{ borderLeft: task.is_offline ? "5px solid #007BFF" : "5px solid #bf2b2e" }}
        >
          {task.is_offline ? "Offline " : "Real-Time "}
          Scenario #{task.id} (vehicles {(task.vehicles || []).map(v => v.id).join(", ")})

          {task.status === "FINISHED" ? (
            <div className="finished-container">
              <span>FINISHED</span>
            </div>
          ) : (
            <button className="connect_button" onClick={() => onProceed(task)}>
              Connect
            </button>
          )}
        </div>
      ))}
      {tasks.length == 0 && <><h2>You have no tasks assigned...</h2></>}
    </div>
  );
};

export default Root;
