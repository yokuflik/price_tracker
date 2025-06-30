import sqlite3
import os
from dotenv import load_dotenv
import models
import pandas as pd

HISTORY_DATA_BASE_FILE = os.getenv("USER_FLIGHT_HISTORY_DATA_BASE_FILE", "user_flight_history.db")

#region debug

def _restartDataBase():
    if os.path.exists(HISTORY_DATA_BASE_FILE):
        os.remove(HISTORY_DATA_BASE_FILE)

def _createRndUsers():
    import random
    res =[]
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
    for i in range(5):
        try_email = f"try{i+1}@gmail.com"
        
        res.append((try_email, models.Flight(user_id=0,
                                departure_airport=airports[random.randint(0,9)], arrival_airport=airports[random.randint(0,9)], 
                                requested_date="2025-07-01", target_price=float(random.randint(6,12)*50))))
        
    return res

def _createRndData():
    us = _createRndUsers()
    for i in us:
        callFuncFromOtherThread(insert_search, i[0], i[1])

def _printAllData():
    conn = sqlite3.connect(HISTORY_DATA_BASE_FILE)
    df = pd.read_sql_query("SELECT * FROM flight_search_history;", conn)
    print(df)
    conn.close()

#endregion

def callFuncFromOtherThread(func, *args, **kwargs):
    #opens the file every time so the file will not stay open when an error occours
    try:
        with sqlite3.connect(HISTORY_DATA_BASE_FILE) as conn:
            cursor = conn.cursor()
            func(cursor, *args, **kwargs)
    except Exception as e:
        print (f"Problem with history data base: {e}")

def make_the_tabel(cursor):
    #make the tabel if not exsist
    create_table_query = """
    CREATE TABLE IF NOT EXISTS flight_search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL DEFAULT (datetime('now')),
        user_email TEXT NOT NULL,
        origin TEXT NOT NULL,
        destination TEXT NOT NULL,
        depart_date TEXT NOT NULL,
        target_price TEXT NOT NULL
    );
    """
    cursor.execute(create_table_query)

def insert_search(cursor, user_id, flight: models.Flight):
    insert_query = """
    INSERT INTO flight_search_history (
        user_email, origin, destination, depart_date, target_price
    ) VALUES (?, ?, ?, ?, ?);
    """

    cursor.execute(insert_query, (
        user_id, flight.departure_airport, flight.arrival_airport, flight.requested_date, flight.target_price
    ))

try:
    callFuncFromOtherThread(make_the_tabel)
except Exception as e:
    print (f"Problem with history data base: {e}")