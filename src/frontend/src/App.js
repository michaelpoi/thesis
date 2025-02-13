import React from "react";
import AuthProvider from "./provider/AuthProvider";
import Routes from "./routes";

function App() {

  // return (
  //   <div className="App">
  //     <h1>Task Manager</h1>
  //     <TaskList onConnect={(task) => setConnectedTask(task)} usedVehicle={usedVehicle} setUsedVehicle={setUsedVehicle} />
  //     {connectedTask && <TaskConnection task={connectedTask} usedVehicle={usedVehicle}/>}
  //   </div>
  // );

    return(
        <AuthProvider>
            <Routes/>
        </AuthProvider>
    )
}

export default App;
