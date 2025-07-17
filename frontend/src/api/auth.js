// src/api/auth.js
import { authenticatedFetch } from './index';

export const registerUser = async (email, password) => {
    return authenticatedFetch('/register_user', {
        method: 'POST',
        body: JSON.stringify({ email, password: password }),
    });
};

export const loginUser = async (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/token`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown login error' }));
        throw new Error(errorData.detail || 'Login failed');
    }

    return response.json();
};