import React, { useState, useEffect } from "react";
import "./task_list.css"
import {useNavigate} from "react-router-dom";
import {fetchWithAuth} from "../utils/api";
import Header from "./Header";

const TaskList = () => {
  const [tasks, setTasks] = useState([]);
  const [newScenarioSteps, setNewScenarioSteps] = useState(0);
  const [newScenarioVehicles, setScenarioVechiles] = useState([{init_x: 0, init_y: 0, init_speed: 0, assigned_user_id:1}]);
  const [showAddScenarioForm, setShowAddScenarioForm] = useState(false);
  const [usedVehicle, setUsedVehicle] = useState(0);
  const [userError, setUserError] = useState(null);
  const navigate = useNavigate();
  const [maps, setMaps] = useState([]);
  const [selectedMap, setSelectedMap] = useState('');


  useEffect(() => {
        fetchWithAuth(`${process.env.REACT_APP_API_URL}/maps/`)
            .then(data => {
                console.log(data)
                if (data){
                    setMaps(data)
                }
            })
    }, []);


  useEffect(() => {
    fetch(`${process.env.REACT_APP_API_URL}/tasks/`)
      .then((res) => res.json())
      .then((data) => setTasks(data));
  }, []);

  const createTask = async () => {
    const res = await fetch(`${process.env.REACT_APP_API_URL}/tasks/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem('token')}` },
      body: JSON.stringify({ steps: newScenarioSteps, vehicles: newScenarioVehicles, map:selectedMap }),
    });
    if (res.status === 401){
        navigate('/logout', {replace: true})
    }
    if (res.status === 400){
        setUserError("User not found")
        return
    }
    const task = await res.json();
    setTasks([...tasks, task]);
    setScenarioVechiles([{init_x: 0, init_y: 0, init_speed: 0, assigned_user_id:1}]);
    setNewScenarioSteps(0);
  };

  const onConnect = (task) => {
      navigate(`/scenario/${task.id}`,{
          state:{task, usedVehicle}
      })
  }

  const onExamine = (task) => {
      navigate(`/result/${task.id}`)
  }

  const onOffline = (task) => {
      navigate(`offline/${task.id}/${usedVehicle}`)
  }

  const handleInputChange = (index, key, value) => {
    setScenarioVechiles((prev) =>
      prev.map((v, i) => (i === index ? { ...v, [key]: value } : v))
    );
  };

  const handleSetAV = (index, vehicle) => {
      if (vehicle.assigned_user_id){
          handleInputChange(index, 'assigned_user_id', null);
      }
      else{
          handleInputChange(index, 'assigned_user_id', 1)
      }

  }

  return (
      <div>
          <label>
              Vehicle
              <input
                  value={usedVehicle}
                  onChange={(e) => setUsedVehicle(e.target.value)}
              />
          </label>

          <div className="scenario_list">
              {tasks.map((task) => (
                  <div key={task.id} className="scenario_card">
                      Scenario #{task.id} (vehicles {task.vehicles.map((vehicle) => (`${vehicle.id} `))})
                      {task.status === 'FINISHED' ?
                          <button className="connect_button" onClick={() => onExamine(task)}>Examine</button>
                          :
                      <button className="connect_button" onClick={() => onConnect(task)}>Connect</button>
                      }

                      <button className="connect_button" onClick={() => onOffline(task)}>Offline</button>

                  </div>
              ))}
          </div>

          {showAddScenarioForm ? (
              <div className="add_scenario">
                  <div className="form_content">
                      <label>
                      Map
                      <select value={selectedMap} onChange={(e) => setSelectedMap(e.target.value)}>
                        <option value="" disabled>Select an option</option>
                            {maps.map((option, index) => (
                        <option key={index} value={option.id}>{option.label}</option>
                        ))}
        </select>
                  </label>
                  <label>
                      Scenario Steps
                      <input
                          value={newScenarioSteps}
                          onChange={(e) => setNewScenarioSteps(e.target.value)}
                          placeholder="Task Steps"
                      />
                  </label>

                  <div id="vehicles">
                      {newScenarioVehicles.map((vehicle, index) => (
                          <div key={index}>
                              <label>
                                  Initial X:
                                  <input
                                      value={vehicle.init_x}
                                      onChange={(e) => handleInputChange(index, "init_x", e.target.value)}
                                  />
                              </label>
                              <label>
                                  Initial Y:
                                  <input
                                      value={vehicle.init_y}
                                      onChange={(e) => handleInputChange(index, "init_y", e.target.value)}
                                  />
                              </label>
                              <label>
                                  Initial Speed:
                                  <input
                                      value={vehicle.init_speed}
                                      onChange={(e) => handleInputChange(index, "init_speed", e.target.value)}
                                  />
                              </label>
                              <label>
                                  Assigned User:
                                  <input
                                    value={vehicle.assigned_user_id}
                                    onChange={(e) => handleInputChange(index, "assigned_user_id", e.target.value)}
                                    disabled={!vehicle.assigned_user_id}
                                  />
                                  {userError && <span style={{ color: "red" }}>{userError}</span>}
                              </label>
                              <label>
                                  Is AV?
                                  <input
                                    type="checkbox"
                                    onChange={() => handleSetAV(index, vehicle)}
                                    checked={!vehicle.assigned_user_id}
                                  />
                              </label>
                          </div>
                      ))}
                      <button onClick={() =>
                          setScenarioVechiles((prev) => [...prev, {init_x: 0, init_y: 0, init_speed: 0, assigned_user_id:1}])
                      }>
                          Add Vehicle
                      </button>
                  </div>

                  <button className="create-task-button" onClick={createTask}>Create Task</button>
                  <button className="close_add_scenario" onClick={() => setShowAddScenarioForm(false)}>Close</button>
                  </div>

              </div>
          ) : (
              <button className="open_add_scenario" onClick={() => setShowAddScenarioForm(true)}>Add Scenario</button>
          )}
      </div>
  );
};

export default TaskList;
