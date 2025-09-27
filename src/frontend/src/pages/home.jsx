import TaskList from "../components/TaskList";
import Header from "../components/Header";
import UsersList from "../components/UsersList";

const Home = () => {


    return (
        <div className="App">
            <Header/>
            <TaskList/>
            <UsersList/>
        </div>
    )
}

export default Home;