import TaskList from "../components/TaskList";
import TaskConnection from "../components/TaskConnection";
import {useState} from "react";
import Header from "../components/Header";

const Home = () => {


    return (
        <div className="App">
            <Header/>
            <h1>Scenarios Manager</h1>
            <TaskList/>
        </div>
    )
}

export default Home;