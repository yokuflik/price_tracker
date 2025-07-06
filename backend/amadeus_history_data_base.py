import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv
import backend.schemas as schemas
load_dotenv()

AMADEUS_HISTORY_DATA_BASE_FILE = os.getenv("AMADEUS_HISTORY_DATA_BASE_FILE", "amadeus_history.db")

def _restartDataBase():
    if os.path.exists(AMADEUS_HISTORY_DATA_BASE_FILE):
        os.remove(AMADEUS_HISTORY_DATA_BASE_FILE)

def _printAllData():
    with sqlite3.connect(AMADEUS_HISTORY_DATA_BASE_FILE) as conn:
        print ("\nFlight search history:\n")
        df = pd.read_sql_query("SELECT * FROM flight_search_history;", conn)
        print(df)

def make_the_tabel(cursor):
    #make the tabel if not exsist
    create_table_query = """
    CREATE TABLE IF NOT EXISTS flight_search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL DEFAULT (datetime('now')),
        origin TEXT NOT NULL,
        destination TEXT NOT NULL,
        depart_date DATE NOT NULL,
        target_price REAL NOT NULL
    );
    """
    cursor.execute(create_table_query)

def callFuncFromOtherThread(func, *args, **kwargs):
    #opens the file every time so the file will not stay open when an error occours
    try:
        with sqlite3.connect(AMADEUS_HISTORY_DATA_BASE_FILE) as conn:
            cursor = conn.cursor()
            func(cursor, *args, **kwargs)
    except Exception as e:
        return {"error": f"Error in data base: {e}"}

#set the tabel in the run of the file
callFuncFromOtherThread(make_the_tabel)

def insert_search(flight: schemas.Flight):
    callFuncFromOtherThread(_insert_search, flight)

    
def _insert_search(cursor, flight: schemas.Flight):
    insert_query = """
    INSERT INTO flight_search_history (origin, destination, depart_date, target_price
    ) VALUES (?, ?, ?, ?);
    """

    cursor.execute(insert_query, (
        flight.departure_airport, flight.arrival_airport, flight.requested_date, flight.target_price
    ))
