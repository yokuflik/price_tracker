// src/components/Navbar.jsx
import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Navbar.css'; // Create this CSS file next

function Navbar() {
    const { isAuthenticated, logout, user } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <nav className="navbar">
            <div className="navbar-brand">
                <Link to="/">Flight Tracker</Link>
            </div>
            <ul className="navbar-nav">
                {isAuthenticated ? (
                    <>
                        <li>
                            <span>Welcome, {user?.email || 'User'}</span>
                        </li>
                        <li>
                            <Link to="/flights">My Flights</Link>
                        </li>
                        <li>
                            <button onClick={handleLogout} className="button link-button">Logout</button>
                        </li>
                    </>
                ) : (
                    <>
                        <li>
                            <Link to="/login">Login</Link>
                        </li>
                        <li>
                            <Link to="/register">Register</Link>
                        </li>
                    </>
                )}
            </ul>
        </nav>
    );
}

export default Navbar;