import sqlite3
from datetime import datetime
import os
import config
from backend.schemas import Flight
import backend.schemas as schemas
from dotenv import load_dotenv
import user_flight_history_data_base as flight_history_db
import bcrypt
from fastapi import HTTPException

DATA_BASE_FILE = os.getenv("DATA_BASE_FILE", "users.db")

#region queries

class queries:

    FLIGHT_COLUMNS = ["departure_airport", "arrival_airport", "requested_date", "target_price",
            "last_checked","last_price_found", "notify_on_any_drop"]

    MORE_CRITERIA_COLUMNS = ["num_connections", "max_connection_hours", "department", "is_round_trip", 
            "return_date", "flexible_days_before", "flexible_days_after","custom_name"]

    BEST_FOUND_COLUMNS = ["best_price", "best_time", "best_airline"]

    ALL_FLIGHT_COLUMNS = FLIGHT_COLUMNS + MORE_CRITERIA_COLUMNS + BEST_FOUND_COLUMNS
    
    create_tracked_flight_tabel_query = """
        CREATE TABLE IF NOT EXISTS tracked_flights (
            flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            departure_airport VARCHAR(3) NOT NULL,
            arrival_airport VARCHAR(3) NOT NULL,
            requested_date DATE NOT NULL,
            target_price DECIMAL(10, 2) NOT NULL,
            last_checked DATETIME,
            last_price_found DECIMAL(10, 2),
            notify_on_any_drop BOOLEAN DEFAULT FALSE,

            num_connections INTEGER,
            max_connection_hours REAL,
            department VARCHAR(255),
            is_round_trip BOOLEAN,
            return_date DATE,
            flexible_days_before INTEGER,
            flexible_days_after INTEGER,
            custom_name TEXT,

            best_price DECIMAL(10, 2),
            best_time VARCHAR(5),
            best_airline VARCHAR(255),

            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """

    get_flight_info_by_user_id_query = f"""
        SELECT flight_id, {', '.join(ALL_FLIGHT_COLUMNS)}
        FROM tracked_flights
        WHERE user_id = ?
    """

    add_flight_query = f"""
            INSERT OR IGNORE INTO tracked_flights (
                user_id, {', '.join(ALL_FLIGHT_COLUMNS)}
            )
            VALUES ({", ".join(["?"] * (len(ALL_FLIGHT_COLUMNS)+1))})
        """

    update_tracked_flight_query = f"""
            UPDATE tracked_flights
            SET {'= ?, '.join(ALL_FLIGHT_COLUMNS) + " = ?"}
            WHERE flight_id = ?
        """

    get_all_flights_info_query = f"""
            SELECT flight_id, 
                user_id, {', '.join(ALL_FLIGHT_COLUMNS)}
            FROM tracked_flights
        """

    def _applyQueryOnFlightValues(cursor, query: str, flight: Flight, on_start_additional_values:tuple = (), on_end_additional_values:tuple = ()):
        """
        gets a query and applys it on all the flight variabels
        """
        
        values = on_start_additional_values + (
            flight.departure_airport,
            flight.arrival_airport,
            flight.requested_date,
            flight.target_price,
            flight.last_checked,
            flight.last_price_found,
            int(flight.notify_on_any_drop),  # boolean to 0/1

            flight.more_criteria.connection,         # 9
            flight.more_criteria.max_connection_hours, # 10
            flight.more_criteria.department,         # 11
            int(flight.more_criteria.is_round_trip),      #12
            flight.more_criteria.return_date,        # 13
            flight.more_criteria.flexible_days_before, # 14
            flight.more_criteria.flexible_days_after, # 15
            flight.more_criteria.custom_name,        # 16

            flight.best_found.price,                         # 17
            flight.best_found.time,                          # 18
            flight.best_found.airline                        # 19
        ) + on_end_additional_values

        cursor.execute(query, values)

#endregion

#region debug funcs

def getAllUsersInfo(cursor, conn) -> str:
    """
    gives all the users and all the flights its a debug func
    """
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    print (len(rows[0]))
    return "\n".join(getUserStringFromTuple(cursor,conn, row) for row in rows)

def getUserStringFromTuple(cursor,conn, tpl : tuple, max_items: int = 6) -> str:
    """
    a debug func that gives a string with the user data and all the user flights
    """
    
    if len(tpl) != 3:
        raise ValueError("Expected a user tuple with 3 elements (id, email, hash_password)")

    user_id, email, hash_password = tpl

    cursor.execute(queries.get_flight_info_by_user_id_query, (user_id,))
    flights = cursor.fetchall()

    result = f"id: {user_id}, email: {email}, hash_password: {hash_password}\n"
    if flights:
        for i, f in enumerate(flights):
            flight_data = dict(f) #get all the flight items like a dict and then add them to the result

            result += f"--- Flight {i+1} ---\n"
            j =0
            for key, value in flight_data.items():
                result += f"  {key}: {value}\n"
                j+=1
                if j == max_items:
                    break
            result += "\n"
    else:
        result += "  No flights tracked.\n"

    return result.strip()

def _createRndUsers():
    """
    a debug func that creates 5 random users and a flight to every user to test the data base
    """
    import random
    for i in range(5):
        try_email = f"try{i+1}@gmail.com"
        callFuncFromOtherThread(addUser, UserInfo(email=try_email, hash_password=f"password{i}"))
        userId = callFuncFromOtherThread(get_user_id_by_email, try_email)
        airports = [
    "JFK",  # John F. Kennedy International Airport, USA
    "LHR",  # London Heathrow Airport, UK
    "CDG",  # Charles de Gaulle Airport, France
    "HND",  # Tokyo Haneda Airport, Japan
    "DXB",  # Dubai International Airport, UAE
    "SYD",  # Sydney Kingsford Smith Airport, Australia
    "GRU",  # São Paulo Guarulhos Airport, Brazil
    "FRA",  # Frankfurt Airport, Germany
    "YYZ",  # Toronto Pearson International Airport, Canada
    "CPT"   # Cape Town International Airport, South Africa
]
        callFuncFromOtherThread(addTrackedFlight, userId, Flight(user_id=userId, 
                                departure_airport=airports[random.randint(0,9)], arrival_airport=airports[random.randint(0,9)], 
                                requested_date="2025-07-07", target_price=random.randint(6,12)*50, 
                                more_criteria = schemas.MoreCriteria(), best_found = schemas.BestFlightFound()))

#endregion

#region control users

def addUser(cursor, conn, user: UserInfo) -> bool:
    cursor.execute("INSERT OR IGNORE INTO users (email, hash_password) VALUES (?, ?)", (user.email,user.hash_password,))
    conn.commit()
    return cursor.rowcount > 0

def get_user_hashed_password_by_email(cursor, conn, email: str) -> str:
    cursor.execute("SELECT hash_password FROM users where email = ?", (email, ))
    res = cursor.fetchone()
    if res is None: return None
    return res[0]

def delete_user(cursor, conn, email: str) -> bool:
    cursor.execute("DELETE FROM users WHERE email = ?", (email,))
    if cursor.rowcount < 0: raise HTTPException(status_code=404, detail=f"{config.USER_NOT_FOUND_ERROR}: {email}")
    conn.commit()
    return True

def get_all_users(cursor, conn) -> list[dict]:
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]  # שמות העמודות

    users = [dict(zip(columns, row)) for row in rows]   # המרה לרשימת מילונים
    return users

def get_user_id_by_email(cursor, conn, email: str) -> int:
    cursor.execute("SELECT id FROM users where email = ?", (email, ))
    res = cursor.fetchone()
    if res is None: return None
    return int(res[0])

def get_user_email_by_id(cursor, conn, user_id: int) -> str:
    cursor.execute("SELECT email FROM users where id = ?", (user_id, ))
    res = cursor.fetchone()
    if res is None: raise HTTPException(status_code=404, detail=f"{config.USER_NOT_FOUND_ERROR}: {user_id}")
    return res[0]

def get_user_id_by_flight_id(cursor, conn, flight_id: int) -> int:
    cursor.execute("SELECT user_id FROM tracked_flights where flight_id = ?", (flight_id, ))
    res = cursor.fetchone()
    if res is None: raise HTTPException(status_code=404, detail=f"Flight: {flight_id} not found")
    return res[0]

#endregion

#region control flights

def addTrackedFlight(cursor, conn,user_id:int, flight: Flight) -> bool:
    #check if the user exists
    get_user_email_by_id(cursor,conn, user_id) #if it will now found it will raise a value error
    
    queries._applyQueryOnFlightValues(cursor, queries.add_flight_query, flight, on_start_additional_values=(user_id,))

    conn.commit()

    #add to the history
    flight_history_db.callFuncFromOtherThread(flight_history_db.insert_search, flight)

    return cursor.rowcount > 0

def updateTrackedFlightDetail(cursor, conn, flight_id: int, flight: Flight) -> bool:
    if flight_id != flight.flight_id: raise HTTPException (status_code=403, detail=f"Forbidden: You cannot update a flight with a differnt flight id flight_id given: {flight_id}, flight.flight_id{flight.flight_id}")
    
    queries._applyQueryOnFlightValues(cursor, queries.update_tracked_flight_query, flight, on_end_additional_values=(flight_id,))

    conn.commit()

    #add to the history
    flight_history_db.callFuncFromOtherThread(flight_history_db.insert_update, flight)

    return cursor.rowcount > 0

def update_all_flight_details(cursor, conn, update_func) -> None:
    """
    Calls `update_func(flight: Flight)` for each tracked flight in the database.
    The function should return a new instance of `Flight` with updated fields.
    """

    cursor.execute(queries.get_all_flights_info_query)

    all_flights = cursor.fetchall()

    for row in all_flights:
        try:
            flight_columns = ["user_id", "flight_id" ] + queries.FLIGHT_COLUMNS
            flight_columns_index = len(flight_columns)
            more_criteria_index= flight_columns_index + len(queries.MORE_CRITERIA_COLUMNS)
            best_found_index = more_criteria_index + len(queries.BEST_FOUND_COLUMNS)

            flight_dict = dict(zip(flight_columns, row[:flight_columns_index]))
            
            more_criteria_dict = dict(zip(queries.MORE_CRITERIA_COLUMNS, row[flight_columns_index:more_criteria_index]))

            best_found_dict = dict(zip(queries.BEST_FOUND_COLUMNS, row[more_criteria_index:best_found_index]))

            flight_dict["more_criteria"] = more_criteria_dict
            flight_dict["best_found"] = best_found_dict

            old_flight = Flight(**flight_dict)

            updated_flight = update_func(old_flight)
            updateTrackedFlightDetail(cursor, conn, old_flight.flight_id, updated_flight)
            
        except Exception as e:
            print(f"Failed updating the flight {row[2]} -> {row[3]} in {row[4]}: {e}")

def getAllUserFlights(cursor,conn, email) -> list[dict]:
    """
    gets a user email and returns a list with all his tracked flights as a list of dicts
    """

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    if result is None:
        raise ValueError(f"{config.USER_NOT_FOUND_ERROR}: {email}")
    user_id = result[0]

    cursor.execute("""
        SELECT * FROM tracked_flights
        WHERE user_id = ?
    """, (user_id,))
    
    flight_tuples = cursor.fetchall() #read from data base
    res = []
    columns = ["flight_id", "user_id"] + queries.ALL_FLIGHT_COLUMNS #addes the 2 id values to get all the values in the SQLite tabel
    for flight_tuple in flight_tuples:
        flight_dict = dict(zip(columns, flight_tuple))
        res.append(flight_dict)

    return res

def deleteFlightById(cursor, conn, flightId:int) -> bool:
    cursor.execute("DELETE FROM tracked_flights WHERE flight_id = ?", (flightId,))
    conn.commit()
    return cursor.rowcount > 0

#endregion

#region main funcs

def _restartDataBase():
    if os.path.exists(DATA_BASE_FILE):
        os.remove(DATA_BASE_FILE)

def _makeTheTabels(cursor, conn):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        hash_password TEXT NOT NULL
    )
    """)

    cursor.execute(queries.create_tracked_flight_tabel_query)

    conn.commit()

def _mainFromFile():
    #_restartDataBase()
    callFuncFromOtherThread(_makeTheTabels)
    _createRndUsers()
    #print(callFuncFromOtherThread(getAllUserFlights, "try5@gmail.com"))
    #print(callFuncFromOtherThread(updateTrackedFlightDetail, 5, Flight(flight_id=5, user_id=5, departure_airport="BKK", 
     #                                                                  arrival_airport="TLV", requested_date="2025-07-03", target_price=1200)))
    #print(callFuncFromOtherThread(getAllUserFlights, "try5@gmail.com"))
    #callFuncFromOtherThread(delete_user, "try3@gmail.com")
    #print (callFuncFromOtherThread(getAllUserFlights, "hey@gmail.com"))
    print (callFuncFromOtherThread(getAllUsersInfo))
    
def callFuncFromOtherThread(func=None, *args, **kwargs):
    #opens the file every time so the file will not stay open when an error occours
    try:
        with sqlite3.connect(DATA_BASE_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if func is not None:
                return func(cursor, conn, *args, **kwargs)
        return None
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Problem in data base {e}")
        
#endregion

if __name__ == "__main__":
    #_mainFromFile()
    pass
    #_restartDataBase()