from sqlalchemy.orm import Session
import pandas as pd
import schemas
import data_base_models as dbm
from connect_to_data_base import get_new_connection

def _printAllData(db: Session):
    query = "SELECT * FROM amadeus_flights;"
    df = pd.read_sql(query, db.bind)
    print(df)

def insert_search(flight: schemas.Flight):
    """Insert a flight search into the Amadeus flight history database."""
    db = get_new_connection() #get connection to the data base

    #convert the flight data to a database model
    flight_to_tabel = dbm.AmadeusFlight(
        departure_airport=flight.departure_airport,
        arrival_airport=flight.arrival_airport,
        requested_date=flight.requested_date,
        target_price=flight.target_price,
        more_criteria=flight.more_criteria)

    db.add(flight_to_tabel)
    db.commit()
