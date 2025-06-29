import sqlite3
from datetime import datetime
import os
import config
from models import Flight, UserInfo
import models
from dotenv import load_dotenv

DATA_BASE_FILE = os.getenv("DATA_BASE_FILE", "users.db")

#region debug funcs

def getAllUsersInfo(cursor, conn):
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    return "\n".join(getUserStringFromTuple(cursor,conn, row) for row in rows)

def getUserStringFromTuple(cursor,conn, tpl):
    if not isinstance(tpl, tuple):
        raise TypeError("Tpl has to be a tuple")
    if len(tpl) != 2:
        raise ValueError("Expected a user tuple with 2 elements (id, email)")

    user_id, email = tpl

    cursor.execute("""
        SELECT id, departure_airport, arrival_airport, requested_date, target_price,
            last_checked,last_price_found, notify_on_any_drop,
            best_price, best_time, best_airline
        FROM tracked_flights
        WHERE user_id = ?
    """, (user_id,))
    flights = cursor.fetchall()

    result = f"id: {user_id}, email: {email}\n"
    if flights:
        for f in flights:
            result += (
                f"  flight_id: {f[0]}\n"
                f"  departure airport: {f[1]}\n"
                f"  arrival airport: {f[2]}\n"
                f"  requested date: {f[3]}\n"
                f"  target price: {f[4]}\n"
            )
            try:
                last_checked_str = f[5] if f[5] else "None"
            except ValueError:
                last_checked_str = f"Invalid date format {f[5]}"
            last_price_found = f[6]
            notify_on_any_drop = bool(f[7])
            best_price = f[8] if f[8] else "None"
            best_time = f[9] if f[9] else "None"
            best_airline = f[10] if f[10] else "None"

            result += (
                f"  last checked: {last_checked_str}\n"
                f"  last best price found: {last_price_found}\n"
                f"  notify on any drop: {notify_on_any_drop}\n"
                f"  best price: {best_price}, time: {best_time}, airline: {best_airline}\n\n"
            )
    else:
        result += "  No flights tracked.\n"

    return result.strip()

def _createRndUsers(cursor, conn):
    import random
    for i in range(5):
        try_email = f"try{i+1}@gmail.com"
        callFuncFromOtherThread(addUser, UserInfo(email=try_email))
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
                                requested_date="2025-07-01", target_price=random.randint(6,12)*50))

#endregion

#region control users

def addUser(cursor, conn, user: UserInfo):
    if not isinstance(user, UserInfo):
        raise TypeError("User must be UserInfo type")
    cursor.execute("INSERT OR IGNORE INTO users (email) VALUES (?)", (user.email,))
    conn.commit()
    return cursor.rowcount > 0

def delete_user(cursor, conn, email: str):
    cursor.execute("DELETE FROM users WHERE email = ?", (email,))
    if cursor.rowcount < 0: raise ValueError(f"{config.USER_NOT_FOUND_ERROR} {email}")
    conn.commit()
    return True

def get_all_users(cursor, conn):
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]  # שמות העמודות

    users = [dict(zip(columns, row)) for row in rows]   # המרה לרשימת מילונים
    return users

def get_user_id_by_email(cursor, conn, email: str):
    cursor.execute("SELECT id FROM users where email = ?", (email, ))
    res = cursor.fetchone()
    if res is None: return None
    return float(res[0])

def get_user_email_by_id(cursor, conn, user_id: float):
    cursor.execute("SELECT email FROM users where id = ?", (user_id, ))
    res = cursor.fetchone()
    if res is None: raise ValueError(f"{config.USER_NOT_FOUND_ERROR} {user_id}")
    return float(res[1])

#endregion

#region control flights

def addTrackedFlight(cursor, conn, user_id, flight: Flight):
    """cursor.execute("SELECT id FROM users WHERE email = ?", (user_email,))
    result = cursor.fetchone()
    if result is None:
        raise ValueError(f"No user found with email {user_email}")
    user_id = result[0]"""

    best_price = None
    best_time = None
    best_airline = None

    if flight.best_found:
        best_price = float(flight.best_found.price)
        best_time = flight.best_found.time
        best_airline = flight.best_found.airline

    cursor.execute("""
        INSERT OR IGNORE INTO tracked_flights (
            user_id, departure_airport, arrival_airport, requested_date, target_price,
            last_checked,last_price_found, notify_on_any_drop,
            best_price, best_time, best_airline
        )
        VALUES (?, ?, ?, ?, ?, ?,?, ?, ?, ?, ?)
    """, (
        user_id,
        flight.departure_airport,
        flight.arrival_airport,
        flight.requested_date,
        flight.target_price,
        flight.last_checked,
        flight.last_price_found,
        int(flight.notify_on_any_drop),  # boolean to 0/1
        best_price,
        best_time,
        best_airline
    ))

    conn.commit()
    return cursor.rowcount > 0

def updateTrackedFlightDetail(cursor, conn, flight_id, flight: Flight):
    best_airline, best_time, best_price = None, None, None

    if flight.best_found: #you need to check if its avaliable because its optional
        best_price = float(flight.best_found.price)
        best_time = flight.best_found.time
        best_airline = flight.best_found.airline

    cursor.execute("""
        UPDATE tracked_flights
        SET departure_airport = ?,
            arrival_airport = ?,
            requested_date = ?,
            target_price = ?,
            last_checked = ?,
            last_price_found = ?,
            notify_on_any_drop = ?,
            best_price = ?,
            best_time = ?,
            best_airline = ?
        WHERE id = ?
    """, (
        flight.departure_airport,
        flight.arrival_airport,
        flight.requested_date,
        flight.target_price,
        flight.last_checked,
        flight.last_price_found,
        flight.notify_on_any_drop,
        best_price,
        best_time,
        best_airline,
        flight_id
    ))
    conn.commit()
    return cursor.rowcount > 0

def update_all_flight_details(cursor, conn, update_func):
    """
    Calls `update_func(flight: Flight)` for each tracked flight in the database.
    The function should return a new instance of `Flight` with updated fields.
    """

    cursor.execute("""
        SELECT id, 
            user_id, 
            departure_airport, 
            arrival_airport, 
            requested_date,
            target_price, 
            last_checked,
            last_price_found,
            notify_on_any_drop, 
            best_price, 
            best_time, 
            best_airline
        FROM tracked_flights
    """)

    all_flights = cursor.fetchall()
    for row in all_flights:
        try:
            # הכנסת השדה של ID (flight_id) מתוך השורה
            flight_id = row[0]
            user_id = row[1]

            old_flight = Flight(
                flight_id=flight_id,
                user_id=user_id,
                departure_airport=row[2],
                arrival_airport=row[3],
                requested_date=row[4],
                target_price=row[5],
                last_checked=row[6],
                last_price_found = row[7],
                notify_on_any_drop=bool(row[8]),
                best_found=models.BestFlightFound(
                    price=float(row[9]), time=row[10], airline=row[11]
                ) if row[9] and row[10] and row[11] else None
            )

            updated_flight = update_func(old_flight)
            updateTrackedFlightDetail(cursor, conn, flight_id, updated_flight)

        except Exception as e:
            print(f"Failed updating the flight {row[2]} -> {row[3]} in {row[4]}: {e}")

def getAllUserFlights(cursor,conn, email):
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    if result is None:
        raise ValueError(f"{config.USER_NOT_FOUND_ERROR} {email}")
    user_id = result[0]

    cursor.execute("""
        SELECT * FROM tracked_flights
        WHERE user_id = ?
    """, (user_id,))
    
    flights = cursor.fetchall()
    return [ # makes a json of all the user flights
        Flight.from_tuple(f).model_dump() for f in flights
    ]

def deleteFlightById(cursor, conn, flightId:float):
    cursor.execute("DELETE FROM tracked_flights WHERE id = ?", (flightId,))
    conn.commit()
    return cursor.rowcount > 0

#endregion

#region main funcs

def _restartDataBase():
    if os.path.exists(DATA_BASE_FILE):
        os.remove(DATA_BASE_FILE)

def makeTheTabels(cursor, conn):
    # טבלת משתמשים לפי אימייל
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL
    )
    """)

    # טבלת טיסות במעקב לפי משתמש
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tracked_flights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        departure_airport TEXT NOT NULL,
        arrival_airport TEXT NOT NULL,
        requested_date TEXT NOT NULL,
        target_price REAL NOT NULL,
        last_checked NULL,
        last_price_found, 
        notify_on_any_drop BOOLEAN NOT NULL DEFAULT 0,
        best_price REAL,
        best_time TEXT,
        best_airline TEXT,
        UNIQUE (user_id, departure_airport, arrival_airport, requested_date),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    conn.commit()

def _mainFromFile():
    callFuncFromOtherThread(makeTheTabels)
    #callFuncFromOtherThread(_createRndUsers)
    #callFuncFromOtherThread(deleteFlightById, 5)
    print(callFuncFromOtherThread(getAllUserFlights, "try2@gmail.com"))
    #callFuncFromOtherThread(_createRndUsers)
    #callFuncFromOtherThread(delete_user, "try3@gmail.com")
    #callFuncFromOtherThread(delete_user, "try4@gmail.com")
    #callFuncFromOtherThread(delete_user, "try5@gmail.com")
    #print (callFuncFromOtherThread(getAllUsersInfo))
    
def callFuncFromOtherThread(func=None, *args, **kwargs):
    with sqlite3.connect(DATA_BASE_FILE) as conn:
        cursor = conn.cursor()
        if func is not None:
            result = func(cursor, conn, *args, **kwargs)
        else:
            result = None
        # אין צורך ב־conn.commit() כאן – הוא קורה אוטומטית אם אין חריגה
    return result

#endregion

if __name__ == "__main__":
    _mainFromFile()
    #_restartDataBase()