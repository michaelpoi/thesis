import { useNavigate } from "react-router-dom";
import { useAuth } from "../provider/AuthProvider";
import {useState} from "react";
import axios from "axios";
import "./login.css"

const Login = () => {
  const { setToken } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    'username': '',
    'password': ''
  })

  const handleLogin = async (e) => {
  e.preventDefault();
    const formParams = new URLSearchParams();
    formParams.append("username", formData.username);
    formParams.append("password", formData.password);

  try{
      const response = await axios.post(`${process.env.REACT_APP_API_URL}/auth/login`, formParams, {
      headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
      }
    });

      const {access_token} = response.data
      setToken(access_token)
      navigate("/", {replace: true})
  }
  catch (error){
      setError("Login or password is incorrect");
  }


    // setToken("this is a test token");
    // navigate("/", { replace: true });
  };

  const handleChange = (e) =>{
    const {name, value} = e.target
    setFormData(
        {
          ...formData,
          [name]: value
        }
    )
  }

  // setTimeout(() => {
  //   handleLogin();
  // }, 3 * 1000);

  return (
    <div className="login-container">
      <h2>Login</h2>
      {error ? <div className="login-error">
        <p>{error}</p>
      </div>: null}
      <form onSubmit={handleLogin} className="login-form">
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="username"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            placeholder="Enter your email"
          />
          {/*{errors.username && <span className="error">{errors.username}</span>}*/}
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Enter your password"
          />
          {/*{errors.password && <span className="error">{errors.password}</span>}*/}
        </div>
        <button type="submit" className="submit-button">
          Login
        </button>
      </form>
        <span>Do not have an account?</span>
        <span><a href="/register">Register here</a></span>
    </div>
  )
};

export default Login;
