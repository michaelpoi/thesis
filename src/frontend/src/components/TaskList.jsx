import React, { useState, useEffect } from "react";

const TaskList = ({ onConnect, usedVehicle, setUsedVehicle }) => {
  const [tasks, setTasks] = useState([]);
  const [newScenarioSteps, setNewScenarioSteps] = useState(0);
  const [newScenarioVehicles, setScenarioVechiles] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/tasks/")
      .then((res) => res.json())
      .then((data) => setTasks(data));
  }, []);

  const createTask = async () => {
    const res = await fetch("http://localhost:8000/tasks/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ steps: newScenarioSteps, vehicles: newScenarioVehicles }),
    });
    const task = await res.json();
    setTasks([...tasks, task]);
    setScenarioVechiles([]);
    setNewScenarioSteps(0);
  };

  const handleInputChange = (index, key, value) => {
    setScenarioVechiles((prev) =>
      prev.map((v, i) => (i === index ? { ...v, [key]: value } : v))
    );
  };

  return (
    <div>
      <h2>Tasks</h2>
      <label>
              Vehicle
              <input value={usedVehicle} onChange={(e) => setUsedVehicle(e.target.value)}></input>
            </label>
      <ul>
        {tasks.map((task) => (
          <li key={task.id}>
            Scenario #{task.id} (vehicles {task.vehicles.map((vehicle) => (`${vehicle.id} `))}) 
            <button onClick={() => onConnect(task)}>Connect</button>
          </li>
        ))}
      </ul>
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
      onChange={(e) => handleInputChange(index, 'init_x', e.target.value)}
    />
  </label>
  <label>
    Initial Y:
    <input
      value={vehicle.init_y}
      onChange={(e) => handleInputChange(index, 'init_y', e.target.value)}
    />
  </label>
  <label>
    Initial Speed:
    <input
      value={vehicle.init_speed}
      onChange={(e) => handleInputChange(index, 'init_speed', e.target.value)}
    />
  </label>
</div>
))}
<button
  onClick={() =>
    setScenarioVechiles((prev) => [...prev, { init_x: 0, init_y: 0, init_speed: 0 }])
  }
>
  Add Vehicle
</button>
      </div>
      <button onClick={createTask}>Create Task</button>
    </div>
  );
};

export default TaskList;
