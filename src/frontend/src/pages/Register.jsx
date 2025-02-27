import { useNavigate } from "react-router-dom";
import { useAuth } from "../provider/AuthProvider";
import {useState} from "react";
import axios from "axios";

const Register = () => {
  const navigate = useNavigate();
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    'username': '',
    'password': ''
  })

  const handleRegister = async (e) => {
  e.preventDefault();

  try{
      const response = await axios.post(`${process.env.REACT_APP_API_URL}/auth/register`, formData, {
    });

      navigate("/login", {replace: true})
  }
  catch (error){
      setError(error);
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
      <form onSubmit={handleRegister} className="login-form">
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="username"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            placeholder="Enter your username"
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
    </div>
  )
};

export default Register;
