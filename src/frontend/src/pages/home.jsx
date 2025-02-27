import TaskList from "../components/TaskList";
import TaskConnection from "../components/TaskConnection";
import {useState} from "react";
import Header from "../components/Header";

const Home = () => {

  const [connectedTask, setConnectedTask] = useState(null);
  const [usedVehicle, setUsedVehicle] = useState(0);


    return (
        <div className="App">
            <Header/>
            <h1>Task Manager</h1>
            <TaskList onConnect={(task) => setConnectedTask(task)} usedVehicle={usedVehicle}
                         setUsedVehicle={setUsedVehicle}/>
            {connectedTask && <TaskConnection task={connectedTask} usedVehicle={usedVehicle}/>}
        </div>
    )
}

export default Home;