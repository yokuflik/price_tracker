// src/components/FlightForm.jsx
import React, { useState, useEffect } from 'react';
import { createFlight, updateFlight } from '../api/flights';
import { useAuth } from '../context/AuthContext';
import './FlightForm.css'; // We'll create this CSS file next

// Hardcoded departments from schemas.py for the frontend demo
const DEPARTMENTS = ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"];

const initialFlightState = {
    departure_airport: '',
    arrival_airport: '',
    requested_date: '',
    target_price: 0,
    notify_on_any_drop: false,
    custom_name: '',
    more_criteria: {
        connection: 0,
        max_connection_hours: null,
        department: DEPARTMENTS[0],
        is_round_trip: true,
        return_date: null,
        flexible_days_before: 0,
        flexible_days_after: 0,
    },
};

function FlightForm({ flightToEdit, onFormSubmit, onCancel }) {
    const { user } = useAuth();
    const [flightData, setFlightData] = useState(initialFlightState);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (flightToEdit) {
            // Initialize form with existing flight data for editing
            setFlightData({
                ...flightToEdit,
                // Ensure nested objects are copied to prevent direct mutation
                more_criteria: { ...flightToEdit.more_criteria },
                // Dates need to be formatted for input type="date"
                requested_date: flightToEdit.requested_date ? new Date(flightToEdit.requested_date).toISOString().split('T')[0] : '',
                return_date: flightToEdit.more_criteria.return_date ? new Date(flightToEdit.more_criteria.return_date).toISOString().split('T')[0] : null,
            });
        } else {
            setFlightData(initialFlightState); // Reset for new flight
        }
        setError(''); // Clear errors when flightToEdit changes
    }, [flightToEdit]);

    const handleMainChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFlightData((prev) => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value,
        }));
    };

    const handleMoreCriteriaChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFlightData((prev) => ({
            ...prev,
            more_criteria: {
                ...prev.more_criteria,
                [name]: type === 'checkbox' ? checked : (type === 'number' ? (value === '' ? null : Number(value)) : value),
            },
        }));
    };

    const validateForm = () => {
        if (!flightData.departure_airport || !flightData.arrival_airport || !flightData.requested_date || flightData.target_price <= 0) {
            setError('Please fill in all required fields (Departure, Arrival, Date, Target Price).');
            return false;
        }
        if (flightData.departure_airport === flightData.arrival_airport) {
            setError('Departure and Arrival airports cannot be the same.');
            return false;
        }
        if (flightData.more_criteria.is_round_trip && !flightData.more_criteria.return_date) {
            setError('Return date is required for round trip flights.');
            return false;
        }
        if (new Date(flightData.requested_date) < new Date(new Date().setHours(0, 0, 0, 0))) { // Check if requested date is in the past
            setError('Requested date cannot be in the past.');
            return false;
        }
        if (flightData.more_criteria.is_round_trip && flightData.more_criteria.return_date && new Date(flightData.more_criteria.return_date) < new Date(flightData.requested_date)) {
            setError('Return date cannot be before the departure date.');
            return false;
        }
        setError('');
        return true;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!validateForm()) {
            return;
        }

        setLoading(true);
        setError('');

        // Prepare data for API call
        const dataToSend = {
            ...flightData,
            // API expects date string, ensure correct format if needed (ISO string should be fine)
            requested_date: flightData.requested_date,
            more_criteria: {
                ...flightData.more_criteria,
                return_date: flightData.more_criteria.is_round_trip ? flightData.more_criteria.return_date : null,
            },
            // API expects user_id for new flights, but not for updates
            // The backend adds user_id from token, but if you send it, ensure it's correct
            // For this demo, let's remove flight_id and user_id for new flight creation,
            // as they are handled by the backend or for update only.
        };

        // Remove user_id and flight_id if they are not meant to be sent from frontend for creation
        if (!flightToEdit) {
            delete dataToSend.flight_id;
            // If your backend *requires* user_id in the payload for creation, and it's derived from `user.id`, add it:
            // dataToSend.user_id = user?.id; 
            // (However, typically for authenticated endpoints, user_id is derived from the token server-side)
        }

        try {
            if (flightToEdit) {
                await updateFlight(flightToEdit.flight_id, dataToSend);
                alert('Flight updated successfully!');
            } else {
                await createFlight(dataToSend);
                alert('Flight added successfully!');
            }
            onFormSubmit(); // Close form and refresh flights
        } catch (err) {
            setError(err.message || 'An error occurred during submission.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flight-form-card">
            <h3>{flightToEdit ? 'Edit Flight' : 'Add New Flight'}</h3>
            <form onSubmit={handleSubmit}>
                {error && <p className="error-message">{error}</p>}

                <div className="form-group">
                    <label htmlFor="custom_name">Custom Name (Optional):</label>
                    <input
                        type="text"
                        id="custom_name"
                        name="custom_name"
                        value={flightData.custom_name || ''}
                        onChange={handleMainChange}
                        placeholder="e.g., My Europe Trip"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="departure_airport">Departure Airport (e.g., TLV):*</label>
                    <input
                        type="text"
                        id="departure_airport"
                        name="departure_airport"
                        value={flightData.departure_airport}
                        onChange={handleMainChange}
                        maxLength="3"
                        required
                        pattern="[A-Z]{3}"
                        title="Please enter a 3-letter IATA airport code (e.g., TLV)"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="arrival_airport">Arrival Airport (e.g., JFK):*</label>
                    <input
                        type="text"
                        id="arrival_airport"
                        name="arrival_airport"
                        value={flightData.arrival_airport}
                        onChange={handleMainChange}
                        maxLength="3"
                        required
                        pattern="[A-Z]{3}"
                        title="Please enter a 3-letter IATA airport code (e.g., JFK)"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="requested_date">Departure Date:*</label>
                    <input
                        type="date"
                        id="requested_date"
                        name="requested_date"
                        value={flightData.requested_date}
                        onChange={handleMainChange}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="target_price">Target Price ($):*</label>
                    <input
                        type="number"
                        id="target_price"
                        name="target_price"
                        value={flightData.target_price || ''}
                        onChange={handleMainChange}
                        min="0.01"
                        step="0.01"
                        required
                    />
                </div>

                <div className="form-group checkbox-group">
                    <input
                        type="checkbox"
                        id="notify_on_any_drop"
                        name="notify_on_any_drop"
                        checked={flightData.notify_on_any_drop}
                        onChange={handleMainChange}
                    />
                    <label htmlFor="notify_on_any_drop">Notify on any price drop (even if not below target)</label>
                </div>

                <h4>More Criteria (Optional)</h4>

                <div className="form-group">
                    <label htmlFor="department">Department:</label>
                    <select
                        id="department"
                        name="department"
                        value={flightData.more_criteria.department}
                        onChange={handleMoreCriteriaChange}
                    >
                        {DEPARTMENTS.map((dept) => (
                            <option key={dept} value={dept}>
                                {dept}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="form-group checkbox-group">
                    <input
                        type="checkbox"
                        id="is_round_trip"
                        name="is_round_trip"
                        checked={flightData.more_criteria.is_round_trip}
                        onChange={handleMoreCriteriaChange}
                    />
                    <label htmlFor="is_round_trip">Is Round Trip?</label>
                </div>

                {flightData.more_criteria.is_round_trip && (
                    <div className="form-group">
                        <label htmlFor="return_date">Return Date:*</label>
                        <input
                            type="date"
                            id="return_date"
                            name="return_date"
                            value={flightData.more_criteria.return_date || ''}
                            onChange={handleMoreCriteriaChange}
                            required={flightData.more_criteria.is_round_trip}
                        />
                    </div>
                )}

                <div className="form-group">
                    <label htmlFor="connection">Max Connections (0 for direct):</label>
                    <input
                        type="number"
                        id="connection"
                        name="connection"
                        value={flightData.more_criteria.connection || 0}
                        onChange={handleMoreCriteriaChange}
                        min="0"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="max_connection_hours">Max Connection Hours (Optional):</label>
                    <input
                        type="number"
                        id="max_connection_hours"
                        name="max_connection_hours"
                        value={flightData.more_criteria.max_connection_hours || ''}
                        onChange={handleMoreCriteriaChange}
                        min="0"
                        step="0.5"
                        placeholder="e.g., 5.5"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="flexible_days_before">Flexible Days Before Departure:</label>
                    <input
                        type="number"
                        id="flexible_days_before"
                        name="flexible_days_before"
                        value={flightData.more_criteria.flexible_days_before || 0}
                        onChange={handleMoreCriteriaChange}
                        min="0"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="flexible_days_after">Flexible Days After Departure:</label>
                    <input
                        type="number"
                        id="flexible_days_after"
                        name="flexible_days_after"
                        value={flightData.more_criteria.flexible_days_after || 0}
                        onChange={handleMoreCriteriaChange}
                        min="0"
                    />
                </div>

                <div className="form-actions">
                    <button type="submit" className="button primary" disabled={loading}>
                        {loading ? 'Saving...' : (flightToEdit ? 'Update Flight' : 'Add Flight')}
                    </button>
                    <button type="button" onClick={onCancel} className="button secondary" disabled={loading}>
                        Cancel
                    </button>
                </div>
            </form>
        </div>
    );
}

export default FlightForm;