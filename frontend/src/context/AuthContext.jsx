// src/context/AuthContext.jsx
import React, { createContext, useState, useEffect, useContext } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null); // Stores user info if logged in (e.g., { email, id })
    const [token, setToken] = useState(localStorage.getItem('token') || null);
    const [loading, setLoading] = useState(true); // To indicate if auth check is in progress

    // Automatically try to re-authenticate from stored token on load
    useEffect(() => {
        if (token) {
            // In a real app, you'd want to validate the token with your backend here
            // For this demo, we'll assume a stored token means logged in
            // You could decode JWT to get user info, or fetch /users/me
            // For simplicity, we'll just set a dummy user if token exists.
            setUser({ email: 'user@example.com', id: 'unknown' }); // Placeholder user
        }
        setLoading(false);
    }, [token]);

    const login = (newToken, userData) => {
        localStorage.setItem('token', newToken);
        setToken(newToken);
        setUser(userData);
    };

    const logout = () => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
    };

    const value = {
        user,
        token,
        loading,
        login,
        logout,
        isAuthenticated: !!token,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
    return useContext(AuthContext);
};