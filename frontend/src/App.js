import React, { useState, useEffect} from "react";

// Base URL for backend API calls
const baseUrl = "http://localhost:8000";

// Example airports list for autocomplete (can be replaced with API data)
const AIRPORTS = [
  { code: "TLV", name: "Tel Aviv - Ben Gurion" },
  { code: "JFK", name: "New York - JFK" },
  { code: "CDG", name: "Paris - Charles de Gaulle" },
  { code: "LHR", name: "London Heathrow" },
  { code: "SFO", name: "San Francisco" },
  { code: "DXB", name: "Dubai International" },
  { code: "HND", name: "Tokyo Haneda" },
  { code: "BKK", name: "Bangkok Suvarnabhumi" },
];

// Autocomplete input component for origin/destination airports
function AutocompleteInput({ label, value, onChange }) {
  const [suggestions, setSuggestions] = React.useState([]);
  const [showSuggestions, setShowSuggestions] = React.useState(false);

  // Filter airports by input value (max 7 results)
  const handleChange = (e) => {
    const val = e.target.value.toUpperCase();
    onChange(val);
    if (val.length === 0) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    const filtered = AIRPORTS.filter(
      (a) => a.code.startsWith(val) || a.name.toUpperCase().includes(val)
    ).slice(0, 7);
    setSuggestions(filtered);
    setShowSuggestions(true);
  };

  // When user clicks a suggestion, fill input with airport code
  const handleSuggestionClick = (code) => {
    onChange(code);
    setSuggestions([]);
    setShowSuggestions(false);
  };

  return (
    <div style={{ marginBottom: "10px", position: "relative" }}>
      <label style={{ display: "block", marginBottom: "5px" }}>{label}</label>
      <input
        type="text"
        value={value}
        onChange={handleChange}
        onFocus={() => value && setShowSuggestions(true)}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 100)} // delay to allow click
        style={{ fontSize: 18, width: "200px", padding: "5px" }}
        placeholder="Airport code or name"
      />
      {showSuggestions && suggestions.length > 0 && (
        <ul
          style={{
            listStyleType: "none",
            margin: 0,
            padding: "5px",
            border: "1px solid #ccc",
            borderTop: "none",
            maxHeight: "150px",
            overflowY: "auto",
            position: "absolute",
            width: "200px",
            backgroundColor: "white",
            zIndex: 1000,
          }}
        >
          {suggestions.map((a) => (
            <li
              key={a.code}
              onClick={() => handleSuggestionClick(a.code)}
              style={{ padding: "5px", cursor: "pointer" }}
            >
              {a.code} - {a.name}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// User input component: input field + search button
function UserInput({ value, onChange, onSearch }) {
  return (
    <div style={{ marginBottom: "20px" }}>
      <label>
        Enter your user IP:&nbsp;
        <input
          type="text"
          value={value}
          onChange={onChange}
          onKeyDown={(e) => {
            if (e.key === "Enter") onSearch(); // trigger search on Enter key
          }}
          placeholder="e.g. 1.2.3.4"
          style={{ fontSize: 20 }}
        />
      </label>
      <button onClick={onSearch} style={{ marginLeft: "15px", fontSize: 20 }}>
        Show Flights
      </button>
    </div>
  );
};

/*
function EditingUI({
  flight,
  editingFlights,
  editingFlightsData,
  setEditingFlightsData,
  deleteFlight,
  updateFlightBtnClick,
}) {
  return (
    <li style={{ marginBottom: "15px", fontSize: 20 }}>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "20px",
          alignItems: "flex-end",
        }}
      >
        { Origin input }
        <div style={{ display: "flex", flexDirection: "column", minWidth: "200px" }}>
          <label style={{ marginBottom: "5px", fontWeight: "bold" }}>Origin</label>
          <AutocompleteInput
            value={editingFlightsData[flight.flight_id]?.departure_airport || ""}
            onChange={(val) =>
              setEditingFlightsData((prev) => ({
                ...prev,
                [flight.flight_id]: {
                  ...prev[flight.flight_id],
                  departure_airport: val,
                },
              }))
            }
          />
        </div>

        {Destination input}
        <div style={{ display: "flex", flexDirection: "column", minWidth: "200px" }}>
          <label style={{ marginBottom: "5px", fontWeight: "bold" }}>Destination</label>
          <AutocompleteInput
            value={editingFlightsData[flight.flight_id]?.arrival_airport || ""}
            onChange={(val) =>
              setEditingFlightsData((prev) => ({
                ...prev,
                [flight.flight_id]: {
                  ...prev[flight.flight_id],
                  arrival_airport: val,
                },
              }))
            }
          />
        </div>

        {Date input }
        <div style={{ display: "flex", flexDirection: "column", minWidth: "200px" }}>
          <label style={{ marginBottom: "5px", fontWeight: "bold" }}>Date</label>
          <input
            type="date"
            value={editingFlightsData[flight.flight_id]?.requested_date || ""}
            onChange={(e) =>
              setEditingFlightsData((prev) => ({
                ...prev,
                [flight.flight_id]: {
                  ...prev[flight.flight_id],
                  requested_date: e.target.value,
                },
              }))
            }
            min={new Date().toISOString().split("T")[0]}
            style={{ fontSize: 18, padding: "5px", width: "100%", fontFamily: "Arial" }}
          />
        </div>

        {Target price input }
        <div style={{ display: "flex", flexDirection: "column", minWidth: "200px" }}>
          <label style={{ marginBottom: "5px", fontWeight: "bold" }}>Target Price ($)</label>
          <input
            type="number"
            min="0"
            step="5"
            value={editingFlightsData[flight.flight_id]?.target_price || ""}
            onChange={(e) =>
              setEditingFlightsData((prev) => ({
                ...prev,
                [flight.flight_id]: {
                  ...prev[flight.flight_id],
                  target_price: e.target.value,
                },
              }))
            }
            style={{ fontSize: 18, padding: "5px", width: "100%" }}
            placeholder="e.g. 300.00"
          />
        </div>

        {Action buttons }
        <button
          onClick={() => deleteFlight(flight.flight_id)}
          style={{ fontSize: 20, marginRight: "10px", marginTop: "10px" }}
        >
          Delete
        </button>
        <button
          onClick={() => updateFlightBtnClick(flight)}
          style={{ fontSize: 20, marginTop: "10px" }}
        >
          {editingFlights.includes(flight.flight_id) ? "Save" : "Update"}
        </button>
      </div>
    </li>
  );
}
*/

function App() {
  const [userId, setUserId] = useState("");
  const [searchingInpId, setSearchingInpId] = useState("");
  const [flights, setFlights] = useState([]); 
  //const [editingFlightsData, setEditingFlightsData] = useState({});
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState(false); 
  //const [editingFlights, setEditingFlights] = useState([]);
  
  // New flight input states
  const [newOrigin, setNewOrigin] = useState("");
  const [newDestination, setNewDestination] = useState("");
  const [newDate, setNewDate] = useState("");
  const [newPrice, setNewPrice] = useState("");

  // Single flight item with details and action buttons
  function FlightItem({ flight}) {
    /*if (editingFlights.includes(flight.flight_id)){
      //get the editing menu
      return (
        <EditingUI
          key={flight.flight_id}
          flight={flight}
          editingFlights={editingFlights}
          editingFlightsData={editingFlightsData}
          setEditingFlightsData={setEditingFlightsData}
          deleteFlight={deleteFlight}
          updateFlightBtnClick={updateFlightBtnClick}
        />
      )
    }*/
    
    //else return the regular view
    return (
      <li style={{ marginBottom: "15px", fontSize: 20 }}>
        <div>
          <strong>From:</strong> {flight.departure_airport} → <strong>To:</strong> {flight.arrival_airport}
        </div>
        <div>
          <strong>Date:</strong> {flight.requested_date} | <strong>Target Price:</strong> ${flight.target_price}
        </div>
        <button
          onClick={() => alert(JSON.stringify(flight, null, 2))}
          style={{ fontSize: 20, marginRight: "10px", marginTop: "10px" }}
        >
          Show Details
        </button>
        <button
          onClick={() => deleteFlight(flight.flight_id)}
          style={{ fontSize: 20, marginRight: "10px", marginTop: "10px" }}
        >
          Delete
        </button>
        {/*<button
          onClick={() => updateFlightBtnClick(flight)}
          style={{ fontSize: 20, marginTop: "10px" }}
        >
          {editingFlights.includes(flight.flight_id) ? "Save" : "Update"}
        </button>*/}
      </li>
    );
  }

  // Flights list component: shows all flights for the user
  function FlightList({ flights, userId}) {
    if (flights.length === 0) return <p>No flights tracked</p>; //if there is no flights
    //make the avaliable flights
    return (
      <div>
        <h2>Tracked Flights for: {userId}</h2>
        <ul>
          {flights.map((flight) => (
            <FlightItem key={flight.flight_id} flight={flight}/>
          ))}
        </ul>
      </div>
    );
  }

  // Fetch flights from the backend API
  const fetchFlights = async () => {
    try {
      const response = await fetch(`${baseUrl}/get_flights?ip=${searchingInpId}`);
      setUserId(searchingInpId); // update displayed userId label
      if (response.status === 404) {
        setError("User not found");
        setFlights([]);
        return;
      }
      if (!response.ok) throw new Error("Failed to fetch flights");
      const data = await response.json();
      setFlights(data);

      setError("");
      setSubmitted(true);
    } catch (err) {
      console.error(err);
      setError("Failed to connect to the server");
    }
  };

  // Delete a flight by flightId
  const deleteFlight = async (flightId) => {
    try {
      const response = await fetch(`${baseUrl}/del_flights?flight_id=${flightId}`, {
        method: "DELETE",
      });
      if (!response.ok) throw new Error("Failed to delete flight");
      fetchFlights(); // refresh flights list after deletion
    } catch (err) {
      console.error(err);
      alert("Could not delete flight");
    }
  };

  /*
  const updateFlightBtnClick = async (flight) => {
    if (editingFlights.includes(flight)){ 
      saveFlightUpdate(flight)
    }
    else{
      openUpdateFlight(flight)
    }
  };

  const openUpdateFlight = async (flight) => {
    setEditingFlights((prev) => [...prev, flight.flight_id]); //add the flight id to the list the view will set outo
    
    const flightToEdit = flights.find((f) => f.flight_id === flight.flight_id);
    setEditingFlightsData((prev) => ({
      ...prev,
      [flight.flight_id]: { ...flightToEdit }, // שמור עותק נפרד לעריכה
    }));
  }

  const saveFlightUpdate = async (flight) => {
    alert ("save")
    const updatedFlight = editingFlightsData[flight.flight_id];
    try {
      const response = await fetch(`${baseUrl}/update_flight`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedFlight),
      });

      if (!response.ok) throw new Error("Failed to update flight");

      setEditingFlights((prev) => prev.filter((id) => id !== updatedFlight.flight_id));
      setEditingFlightsData((prev) => {
        const newData = { ...prev };
        delete newData[updatedFlight.flight_id];
        return newData;
      });

      fetchFlights(); // refresh flights list after updating
    } catch (err) {
      console.error(err);
      alert("Could not update flight");
    }
  }*/

  // Add new flight
  const addFlight = async () => {
    // Basic validation: all fields must be filled
    if (!newOrigin || !newDestination || !newDate || !newPrice) {
      alert("Please fill all fields");
      return;
    }

    //check if the destintion and origin is the same
    if (newOrigin === newDestination){
      alert("Destination and origin can't be the same");
      return;
    }

    // Prepare flight data
    const flightData = {
      ip: userId, // the user IP to associate the flight with
      departure_airport: newOrigin,
      arrival_airport: newDestination,
      requested_date: newDate,
      target_price: parseFloat(newPrice),
    };

    try {
      const response = await fetch(`${baseUrl}/add_flight`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(flightData),
      });
      if (!response.ok) throw new Error("Failed to add flight");

      // Refresh flights list after adding
      fetchFlights();

      // Clear input fields
      setNewOrigin("");
      setNewDestination("");
      setNewDate("");
      setNewPrice("");
    } catch (err) {
      console.error(err);
      alert("Failed to add flight");
    }
  };

  //the html part
  return (
    <div style={{ padding: "20px", fontFamily: "Arial", fontSize: 20 }}>
      <h1>Flight Tracker</h1>

      {/* User input for IP */}
      <UserInput value={searchingInpId} onChange={(e) => setSearchingInpId(e.target.value)} onSearch={fetchFlights} />

      {/* Show error message if any */}
      {error && <p style={{ color: "red" }}>{error}</p>}

      {/* Flights list */}
      {submitted && !error && (
        <>
          <FlightList flights={flights} userId={userId}/>

          {/* Add new flight section */}
          <div style={{ marginTop: "30px", borderTop: "1px solid #ccc", paddingTop: "20px" }}>
            <h3>Add New Flight</h3>

            {/* Inputs in a single row */}
            <div style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "20px",
              alignItems: "flex-end",  // Align inputs by their bottom (works well for label+input)
              justifyContent: "center" // Optional: center the row
            }}>
              {/* Origin input */}
              <div style={{ display: "flex", flexDirection: "column", minWidth: "200px" }}>
                <label style={{ marginBottom: "5px", fontWeight: "bold" }}>Origin</label>
                <AutocompleteInput value={newOrigin} onChange={setNewOrigin} />
              </div>

              {/* Destination input */}
              <div style={{ display: "flex", flexDirection: "column", minWidth: "200px" }}>
                <label style={{ marginBottom: "5px", fontWeight: "bold" }}>Destination</label>
                <AutocompleteInput value={newDestination} onChange={setNewDestination} />
              </div>

              {/* Date input */}
              <div style={{ display: "flex", flexDirection: "column", minWidth: "200px" }}>
                <label style={{ marginBottom: "5px", fontWeight: "bold" }}>Date</label>
                <input
                  type="date"
                  value={newDate}
                  onChange={(e) => setNewDate(e.target.value)}
                  min={new Date().toISOString().split("T")[0]} // only future dates
                  style={{ fontSize: 18, padding: "5px", width: "100%", fontFamily: "Arial" }}
                />
              </div>

              {/* Target price input */}
              <div style={{ display: "flex", flexDirection: "column", minWidth: "200px" }}>
                <label style={{ marginBottom: "5px", fontWeight: "bold" }}>Target Price ($)</label>
                <input
                  type="number"
                  min="0"
                  step="5"
                  value={newPrice}
                  onChange={(e) => setNewPrice(e.target.value)}
                  style={{ fontSize: 18, padding: "5px", width: "100%" }}
                  placeholder="e.g. 300.00"
                />
              </div>
            </div>

            {/* Button centered below the row */}
            <div style={{ marginTop: "20px", textAlign: "center" }}>
              <button onClick={addFlight} style={{ fontSize: 20, padding: "10px 25px" }}>
                Add Flight
              </button>
            </div>
          </div>

        </>
      )}
    </div>
  );
}

export default App;
