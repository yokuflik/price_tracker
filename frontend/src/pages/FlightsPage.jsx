// src/pages/FlightsPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { getMyFlights, deleteFlight } from '../api/flights';
import FlightForm from '../components/FlightForm'; // We will create this next
import './FlightsPage.css'; // Create this CSS file next

function FlightsPage(email) {
    const { token, isAuthenticated } = useAuth();
    const [flights, setFlights] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [showForm, setShowForm] = useState(false);
    const [editingFlight, setEditingFlight] = useState(null); // Will hold flight data if editing

    const fetchFlights = useCallback(async () => {
        if (!isAuthenticated || !token) {
            setLoading(false);
            return;
        }
        setLoading(true);
        setError('');
        try {
            const data = await getMyFlights(email);
            setFlights(data);
        } catch (err) {
            setError(err.message || 'Failed to fetch flights.');
            setFlights([]); // Clear flights on error
        } finally {
            setLoading(false);
        }
    }, [isAuthenticated, token]);

    useEffect(() => {
        fetchFlights();
    }, [fetchFlights]);

    const handleDelete = async (flightId) => {
        if (window.confirm('Are you sure you want to delete this flight tracking?')) {
            setError('');
            try {
                await deleteFlight(flightId);
                setFlights(flights.filter((flight) => flight.flight_id !== flightId));
                alert('Flight deleted successfully!');
            } catch (err) {
                setError(err.message || 'Failed to delete flight.');
            }
        }
    };

    const handleAddFlightClick = () => {
        setEditingFlight(null); // Ensure we're adding a new flight
        setShowForm(true);
    };

    const handleEditFlightClick = (flight) => {
        setEditingFlight(flight); // Set flight data for editing
        setShowForm(true);
    };

    const handleFormClose = () => {
        setShowForm(false);
        setEditingFlight(null); // Clear editing state
        fetchFlights(); // Refresh flights after add/edit/cancel
    };

    if (loading) {
        return <div className="container">Loading flights...</div>;
    }

    if (error) {
        return <div className="container error-message">{error}</div>;
    }

    return (
        <div className="container">
            <div className="flights-header">
                <h2>My Tracked Flights</h2>
                <button onClick={handleAddFlightClick} className="button primary">
                    Add New Flight
                </button>
            </div>

            {showForm && (
                <div className="flight-form-modal-overlay">
                    <div className="flight-form-modal">
                        <FlightForm flightToEdit={editingFlight} onFormSubmit={handleFormClose} onCancel={handleFormClose} />
                    </div>
                </div>
            )}

            {flights.length === 0 && !showForm ? (
                <p>No flights tracked yet. Click "Add New Flight" to get started!</p>
            ) : (
                <div className="flight-list">
                    {flights.map((flight) => (
                        <div key={flight.flight_id} className="flight-card">
                            <h3>{flight.custom_name || `${flight.departure_airport} to ${flight.arrival_airport}`}</h3>
                            <p>
                                <strong>Route:</strong> {flight.departure_airport} &rarr; {flight.arrival_airport}
                            </p>
                            <p>
                                <strong>Date:</strong> {flight.requested_date} {flight.more_criteria.is_round_trip ? `(Return: ${flight.more_criteria.return_date || 'N/A'})` : ''}
                            </p>
                            <p>
                                <strong>Target Price:</strong> ${flight.target_price}
                            </p>
                            <p>
                                <strong>Last Found Price:</strong> {flight.last_price_found ? `$${flight.last_price_found}` : 'N/A'}
                                {flight.last_checked && ` (Last checked: ${new Date(flight.last_checked).toLocaleString()})`}
                            </p>
                            {flight.best_found && flight.best_found.price && (
                                <p>
                                    <strong>Best Price Found:</strong> ${flight.best_found.price} (on {flight.best_found.time ? new Date(flight.best_found.time).toLocaleDateString() : 'N/A'} by {flight.best_found.airline || 'N/A'})
                                </p>
                            )}
                            <div className="flight-card-actions">
                                <button onClick={() => handleEditFlightClick(flight)} className="button secondary">
                                    Edit
                                </button>
                                <button onClick={() => handleDelete(flight.flight_id)} className="button danger">
                                    Delete
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default FlightsPage;