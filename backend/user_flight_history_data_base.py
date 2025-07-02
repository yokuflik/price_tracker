import sqlite3
import os
from dotenv import load_dotenv
import models
import pandas as pd
import logging

HISTORY_DATA_BASE_FILE = os.getenv("USER_FLIGHT_HISTORY_DATA_BASE_FILE", "user_flight_history.db")

#region logger

FLIGHT_HISTORY_DB_LOG_FILE_PATH = os.getenv("UPDATE_IN_SERVER_LOG_FILE_PATH", "update_in_server.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

#set the dir
log_dir = os.path.dirname(FLIGHT_HISTORY_DB_LOG_FILE_PATH)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(FLIGHT_HISTORY_DB_LOG_FILE_PATH, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

#endregion

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
        callFuncFromOtherThread(insert_search, i[1])

def _printAllData():
    with sqlite3.connect(HISTORY_DATA_BASE_FILE) as conn:

        print ("\nFlight search history:\n")
        df = pd.read_sql_query("SELECT * FROM flight_search_history;", conn)
        print(df)

        print ("\nFlight update history:\n")
        df = pd.read_sql_query("SELECT * FROM flight_update_history;", conn)
        print(df)


#endregion

def callFuncFromOtherThread(func, *args, **kwargs):
    #opens the file every time so the file will not stay open when an error occours
    try:
        with sqlite3.connect(HISTORY_DATA_BASE_FILE) as conn:
            cursor = conn.cursor()
            func(cursor, *args, **kwargs)
    except Exception as e:
        logger.error(f"Error in data base: {e}")

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

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS flight_update_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL DEFAULT (datetime('now')),
        origin TEXT NOT NULL,
        destination TEXT NOT NULL,
        depart_date DATE NOT NULL,
        target_price REAL NOT NULL
    );"""
    )

def insert_search(cursor, flight: models.Flight):
    insert_query = """
    INSERT INTO flight_search_history (origin, destination, depart_date, target_price
    ) VALUES (?, ?, ?, ?);
    """

    cursor.execute(insert_query, (
        flight.departure_airport, flight.arrival_airport, flight.requested_date, flight.target_price
    ))

def insert_update(cursor, flight: models.Flight):
    insert_query = """
    INSERT INTO flight_update_history (origin, destination, depart_date, target_price
    ) VALUES (?, ?, ?, ?);
    """

    cursor.execute(insert_query, (
        flight.departure_airport, flight.arrival_airport, flight.requested_date, flight.target_price
    ))

try:
    #_restartDataBase()
    callFuncFromOtherThread(make_the_tabel)
    #_createRndData()
    #_printAllData()
except Exception as e:
    logger.error(f"Error in data base: {e}")