// src/pages/RegisterPage.jsx
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext'; // Make sure this path is correct
import { registerUser } from '../api/auth'; // Make sure this path is correct
import '../Auth.css'; // Make sure this path is correct

function RegisterPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    // Ensure 'login' is correctly destructured from useAuth
    const { login } = useAuth(); // THIS IS THE CRUCIAL LINE for the fix

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            // 1. Call the backend's register endpoint
            const registrationResult = await registerUser(email, password);

            // Assuming registerUser either returns a success/user object
            // or throws an error if registration fails.
            // If registration is successful, then we proceed to log the user in.
            if (registrationResult) { // Check if registration was conceptually successful
                // 2. Call the login function from AuthContext to set user state and token
                await login(email, password); // Use the 'login' function we got from useAuth
                navigate('/flights'); // Redirect on success
            } else {
                // This path might be hit if registerUser returns null/false but doesn't throw
                setError('Registration failed without specific error message.');
            }
        } catch (err) {
            // Catch any errors from either registerUser or login
            setError(err.message || 'An unexpected error occurred during registration.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container auth-container">
            <div className="form-card">
                <h2>Register</h2>
                <form onSubmit={handleSubmit}>
                    {error && <p className="error-message">{error}</p>}
                    <div className="form-group">
                        <label htmlFor="email">Email:</label>
                        <input
                            type="email"
                            id="email"
                            name="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="password">Password:</label>
                        <input
                            type="password"
                            id="password"
                            name="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>
                    <button type="submit" className="button primary" disabled={loading}>
                        {loading ? 'Registering...' : 'Register'}
                    </button>
                </form>
                <p className="auth-switch">
                    Already have an account? <Link to="/login">Login here</Link>
                </p>
            </div>
        </div>
    );
}

export default RegisterPage;