// src/api/flights.js
import { authenticatedFetch } from './index';

export const getMyFlights = async (email) => {
    return authenticatedFetch('/get_flights/me', {
        method: 'GET',
        body: JSON.stringify({ email: email || '' }),
    });
};

export const createFlight = async (flightData) => {
    return authenticatedFetch('/flights/', {
        method: 'POST',
        body: JSON.stringify(flightData),
    });
};

export const updateFlight = async (flightId, flightData) => {
    return authenticatedFetch(`/flights/${flightId}`, {
        method: 'PUT',
        body: JSON.stringify(flightData),
    });
};

export const deleteFlight = async (flightId) => {
    return authenticatedFetch(`/flights/${flightId}`, {
        method: 'DELETE',
    });
};