import {useNavigate} from "react-router-dom";

const Header = ({username}) =>{

    const navigate = useNavigate();



    return (<div className="header">
        {username ? (
            <div>You are logged in as {username}</div>
        ): (
            <div>
                <button onClick={() => navigate("/login", {replace:true})}>Login</button>
                <button onClick={() => navigate("/register", {replace: true})}>Register</button>
            </div>
        )}
    </div>);
}

export default Header;