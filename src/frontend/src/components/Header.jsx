import React, { useState, useEffect } from "react";
import "./header.css";
import {fetchWithAuth} from "../utils/api";
import {useNavigate} from "react-router-dom";

const Header = () => {
  const [showMenu, setShowMenu] = useState(false);
  const [username, setUsername] = useState(null);
  const navigate = useNavigate();

    useEffect(() => {
        fetchWithAuth(`${process.env.REACT_APP_API_URL}/auth/me/`)
            .then(data => setUsername(data.username))
    }, []);

  return (
    <header className="header">
      <h1>MetaSimulator</h1>

      <nav className="nav">
        {/* Maps Dropdown */}
        <div className="dropdown">
          <button
            className="nav_button"
            onClick={() => setShowMenu(!showMenu)}
          >
            Maps ▾
          </button>
          {showMenu && (
            <div className="dropdown_menu">
              <a href="/maps">Map List</a>
              <a href="/creator">Map Creator</a>
            </div>
          )}
        </div>

        {username && (
          <span className="username">Hello, {username}!</span>
        )}

        {/* Login / Logout Button */}
        {username ? (
          <button className="auth_button logout" onClick={() => navigate('/logout', {replace:true})}>
            Logout
          </button>
        ) : (
          <button className="auth_button login" onClick={() => navigate('/login', {replace: true})}>
            Login
          </button>
        )}
      </nav>
    </header>
  );
};

export default Header;