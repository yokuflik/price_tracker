import sqlite3
from datetime import datetime
import os
import atexit

DATABASEFILE = "users.db"

# Connect to the database file
conn = sqlite3.connect(DATABASEFILE)
cursor = conn.cursor()

# Ensures the connection is committed and closed when the program exits normally
@atexit.register
def close_connection():
    if conn:
        conn.commit()
        conn.close()

class UserInfo:
    def __init__(self, ip_address):
        self.ip_address = ip_address

class Flight:
    def __init__(self, ip: str, departure_airport: str, arrival_airport: str, requested_date: str, target_price: float, last_checked=None, last_checked_price=None):
        self.ip = ip
        self.departure_airport = departure_airport
        self.arrival_airport = arrival_airport
        self.requested_date = requested_date
        self.target_price = target_price
        self.last_checked = last_checked
        self.last_checked_price = last_checked_price
    
    @classmethod
    def fromTupel(cls, tpl: tuple):
        if len(tpl) != 8: 
            raise Exception('Problem with the tupel length')
        return Flight(tpl[1], tpl[2], tpl[3], tpl[4], tpl[5], tpl[6], tpl[7])

#region debug funcs

def getAllUsers():
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    return "\n".join(getUserStringFromTuple(row) for row in rows)

def getUserStringFromTuple(tpl):
    if not isinstance(tpl, tuple):
        raise TypeError("Tpl has to be a tuple")
    if len(tpl) != 2:
        raise ValueError("Expected a user tuple with 2 elements (id, ip_address)")

    user_id, ip = tpl

    cursor.execute("""
        SELECT departure_airport, arrival_airport, requested_date, target_price, last_checked, last_checked_price
        FROM tracked_flights
        WHERE user_id = ?
    """, (user_id,))
    flights = cursor.fetchall()

    result = f"id: {user_id}, ip_address: {ip}\n"
    if flights:
        for f in flights:
            result += (
                f"  departure airport: {f[0]}\n"
                f"  arrival airport: {f[1]}\n"
                f"  requested date: {f[2]}\n"
                f"  target price: {f[3]}\n"
            )
            if f[4]:
                dt_obj = datetime.fromisoformat(f[4])
                last_checked_str = dt_obj.strftime("%d/%m/%Y %H:%M:%S")
            else:
                last_checked_str = "None"

            last_checked_price_str = f[5] if f[5] is not None else "None"

            result += (
                f"  last checked: {last_checked_str}\n"
                f"  last checked price: {last_checked_price_str}\n\n"
            )
    else:
        result += "  No flights tracked.\n"

    return result.strip()

#endregion

#region control users

def addUser(user: UserInfo):
    if not isinstance(user, UserInfo):
        raise TypeError("user must be UserInfo type")
    cursor.execute("INSERT OR IGNORE INTO users (ip_address) VALUES (?)", (user.ip_address,))
    conn.commit()
    return cursor.rowcount > 0

def delete_user(ip: str):
    cursor.execute("DELETE FROM users WHERE ip_address = ?", (ip,))
    conn.commit()
    return cursor.rowcount > 0

#endregion

#region control flights

def addTrackedFlight(flight: Flight):
    if not isinstance(flight, Flight):
        raise TypeError("flight must be Flight type")

    cursor.execute("SELECT id FROM users WHERE ip_address = ?", (flight.ip,))
    result = cursor.fetchone()
    if result is None:
        raise ValueError(f"No user found with IP {flight.ip}")
    user_id = result[0]

    cursor.execute("""
        INSERT OR IGNORE INTO tracked_flights (user_id, departure_airport, arrival_airport, requested_date, target_price, last_checked, last_checked_price)
        VALUES (?, ?, ?, ?, ?, NULL, NULL)
    """, (user_id, flight.departure_airport, flight.arrival_airport, flight.requested_date, flight.target_price))

    conn.commit()
    return cursor.rowcount > 0

def updateTrackedFlightDetail(ip, flight: Flight):
    if not isinstance(flight, Flight):
        raise TypeError("flight must be Flight type")
    if ip != flight.ip:
        raise Exception("Can't change a flight with a different IP")

    cursor.execute("SELECT id FROM users WHERE ip_address = ?", (ip,))
    result = cursor.fetchone()
    if result is None:
        raise ValueError(f"No user found with IP {ip}")
    user_id = result[0]

    cursor.execute("""
        INSERT INTO tracked_flights (user_id, departure_airport, arrival_airport, requested_date, target_price, last_checked, last_checked_price)
        VALUES (?, ?, ?, ?, ?, NULL, NULL)
        ON CONFLICT(user_id, departure_airport, arrival_airport, requested_date)
        DO UPDATE SET
            target_price = excluded.target_price,
            departure_airport = excluded.departure_airport,
            arrival_airport = excluded.arrival_airport,
            requested_date = excluded.requested_date
    """, (user_id, flight.departure_airport, flight.arrival_airport, flight.requested_date, flight.target_price))
    conn.commit()

def updateFlightCheckTime(departure_airport, arrival_airport, requested_date, time = datetime.now().isoformat()):
    cursor.execute("""
        UPDATE tracked_flights
        SET last_checked = ?, last_checked_price = NULL
        WHERE departure_airport = ? AND arrival_airport = ? AND requested_date = ?
    """, (time, departure_airport, arrival_airport, requested_date))
    conn.commit()

def updateFlightCheckPrice(departure_airport, arrival_airport, requested_date, price_str):
    """
    Updates last_checked with current time and last_checked_price with the given price string.
    """
    now_iso = datetime.now().isoformat()
    cursor.execute("""
        UPDATE tracked_flights
        SET last_checked = ?, last_checked_price = ?
        WHERE departure_airport = ? AND arrival_airport = ? AND requested_date = ?
    """, (now_iso, price_str, departure_airport, arrival_airport, requested_date))
    conn.commit()

def update_all_flight_details(update_func):
    """
    קוראת לפונקציה `update_func(flight: Flight)` עבור כל טיסה במעקב.
    הפונקציה צריכה להחזיר מופע חדש של `Flight` עם שדות מעודכנים (כולל last_checked ו־last_checked_price).
    """
    cursor.execute("""
        SELECT id, user_id, departure_airport, arrival_airport, requested_date, target_price, last_checked, last_checked_price
        FROM tracked_flights
    """)
    all_flights = cursor.fetchall()

    for row in all_flights:
        try:
            old_flight = Flight.fromTupel(row)
            updated_flight = update_func(old_flight)
            updateFlightDetail(updated_flight, row)
        except Exception as e:
            print(f"Failed updating the flight {row[2]} -> {row[3]} in {row[4]}: {e}")
            raise e

def updateFlightDetail(updated_flight: Flight, row):
    if isinstance(updated_flight, Flight):
        cursor.execute("""
            UPDATE tracked_flights
            SET last_checked = ?, last_checked_price = ?, target_price = ?
            WHERE user_id = ? AND departure_airport = ? AND arrival_airport = ? AND requested_date = ?
        """, (
            updated_flight.last_checked,
            updated_flight.last_checked_price,
            updated_flight.target_price,
            row[1],  # user_id
            updated_flight.departure_airport,
            updated_flight.arrival_airport,
            updated_flight.requested_date
        ))
        conn.commit()
    else:
        raise TypeError("Flight to update wasnt Flight type")

def deleteUserFlight(ip, departure_airport, arrival_airport, requested_date):
    cursor.execute("SELECT id FROM users WHERE ip_address = ?", (ip,))
    result = cursor.fetchone()
    if result is None:
        raise ValueError(f"No user found with IP {ip}")
    user_id = result[0]

    cursor.execute("""
        DELETE FROM tracked_flights
        WHERE user_id = ? AND departure_airport = ? AND arrival_airport = ? AND requested_date = ?
    """, (user_id, departure_airport, arrival_airport, requested_date))

    conn.commit()
    return cursor.rowcount > 0

def getUserFlight(ip, departure_airport, arrival_airport, requested_date):
    cursor.execute("SELECT id FROM users WHERE ip_address = ?", (ip,))
    result = cursor.fetchone()
    if result is None:
        raise ValueError(f"No user found with IP {ip}")
    user_id = result[0]

    cursor.execute("""
        SELECT * FROM tracked_flights
        WHERE user_id = ? AND departure_airport = ? AND arrival_airport = ? AND requested_date = ?
    """, (user_id, departure_airport, arrival_airport, requested_date))

    flight = cursor.fetchone()
    if flight is None:
        return None

    return {
        "flight_id": flight[0],
        "user_id": flight[1],
        "departure_airport": flight[2],
        "arrival_airport": flight[3],
        "requested_date": flight[4],
        "target_price": flight[5],
        "last_checked": flight[6],
        "last_checked_price": flight[7]
    }

def getAllUserFlights(ip):
    cursor.execute("SELECT id FROM users WHERE ip_address = ?", (ip,))
    result = cursor.fetchone()
    if result is None:
        raise ValueError(f"No user found with IP {ip}")
    user_id = result[0]

    cursor.execute("""
        SELECT * FROM tracked_flights
        WHERE user_id = ?
    """, (user_id,))
    
    flights = cursor.fetchall()
    return [
        {
            "flight_id": f[0],
            "user_id": f[1],
            "departure_airport": f[2],
            "arrival_airport": f[3],
            "requested_date": f[4],
            "target_price": f[5],
            "last_checked": f[6],
            "last_checked_price": f[7]
        }
        for f in flights
    ]

#endregion

#region main funcs

def _restartDataBase():
    if os.path.exists(DATABASEFILE):
        os.remove(DATABASEFILE)

def makeTheTabels():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip_address TEXT UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tracked_flights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        departure_airport TEXT,
        arrival_airport TEXT,
        requested_date TEXT,
        target_price REAL,
        last_checked TEXT,
        last_checked_price REAL,
        UNIQUE (user_id, departure_airport, arrival_airport, requested_date),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    conn.commit()

def _mainFromFile():
    makeTheTabels()

    ip = "1.2.3.4"
    addUser(UserInfo(ip))
    addTrackedFlight(Flight(ip, "TLV", "CDG", "2025-07-01", 350.00))
    updateTrackedFlightDetail(ip, Flight(ip, "TLV", "CDG", "2025-07-01", 300.00))
    updateTrackedFlightDetail(ip, Flight(ip, "TLV", "CDG", "2025-07-02", 300.00))
    print(getAllUsers())

#endregion

if __name__ == "__main__":
    _mainFromFile()
