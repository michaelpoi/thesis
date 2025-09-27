import { useState, useEffect } from 'react';
import { fetchWithAuth } from "../utils/api";
import "./task_list.css";
import { useNavigate } from "react-router-dom";


const UsersList = () => {

    const [users, setUsers] = useState([]);
    const [newUserUsername, setNewUserUsername] = useState('');
    const [newUserPassword, setNewUserPassword] = useState('');
    const [newUserIsAdmin, setNewUserIsAdmin] = useState(false);
    const [showAddUserForm, setShowAddUserForm] = useState(false);
    const [addUserError, setAddUserError] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        fetchWithAuth(`${process.env.REACT_APP_API_URL}/users/`)
            .then(data => {
                console.log(data)
                if (data) {
                    setUsers(data);
                }
            })
    }, []);

    const createUser = async () => {
        const res = await fetch(`${process.env.REACT_APP_API_URL}/users/`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem('token')}` },
            body: JSON.stringify({ username: newUserUsername, password: newUserPassword, is_admin: newUserIsAdmin }),
        });
        if (res.status === 401) {
            navigate('/logout', { replace: true })
            return;
        }
        const user = await res.json();
        if (res.status === 400) {
            setAddUserError(user.detail);
            return
        }

        setUsers(prev => [...prev, user]);
        setNewUserIsAdmin(false);
        setNewUserUsername('');
        setNewUserPassword('');
        setAddUserError(null);
    }

    const removeUser = async (uid) => {
        const res = await fetch(`${process.env.REACT_APP_API_URL}/users/${uid}/`, {
            method: "DELETE",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem('token')}` },
        });

        if (res.ok) {
            setUsers(prev => prev.filter(user => user.id !== uid));
        } else {
            console.error("Failed to delete user:", res.status);
        }
    }

    return (
        <div>
            <h1>Users</h1>
            <div className="scenario_list">
                {users.map((user) => (
                    <div key={user.id} className="scenario_card" style={{ borderLeft: user.is_admin ? "5px solid #007BFF" : "5px solid #bf2b2eff" }}>
                        <span>{user.is_admin ? "Admin " : "Non-admin "}User #{user.id} </span>
                        <span>{user.username}</span>
                        <button className="remove_button" onClick={() => removeUser(user.id)}>Delete</button>

                    </div>
                ))}
            </div>

            {showAddUserForm ? (
                <div className="add_scenario">

                    <div className="form_content">

                        {addUserError && <span style={{ color: "red" }}>{addUserError}</span>}

                        <label>
                            Username
                            <input
                                value={newUserUsername}
                                onChange={(e) => setNewUserUsername(e.target.value)}
                                placeholder="username"
                            />
                        </label>

                        <label>
                            Password
                            <input
                                value={newUserPassword}
                                onChange={(e) => setNewUserPassword(e.target.value)}
                                placeholder="password"
                            />
                        </label>

                        <label>
                            Admin
                            <input
                                type="checkbox"
                                onChange={(e) => setNewUserIsAdmin(e.target.checked)}
                                checked={newUserIsAdmin}
                            />
                        </label>



                        <button className="create-task-button" onClick={createUser}>Create User</button>
                        <button className="close_add_scenario" onClick={() => setShowAddUserForm(false)}>Close</button>
                    </div>

                </div>
            ) : (
                <button className="open_add_scenario" onClick={() => setShowAddUserForm(true)}>Add User</button>
            )}
        </div>

    );
}

export default UsersList;