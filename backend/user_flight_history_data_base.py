import os
from dotenv import load_dotenv
from requests import Session
import schemas
import pandas as pd
import logging

import data_base_models as dbm
from connect_to_data_base import get_new_connection
from config import settings

#region logger

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(f"{settings.LOGGOR_FOLDER_PATH}/flight_history_db_logger.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

#endregion

#region debug

def _createRndFlights(db: Session) -> list[dbm.AddFlight]:
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
        res.append(dbm.AddFlight(departure_airport=airports[random.randint(0,9)], arrival_airport=airports[random.randint(0,9)], 
                                requested_date="2025-07-01", target_price=float(random.randint(6,12)*50)))
        
    return res

def _createRndData(db: Session):
    us = _createRndFlights(db)
    for i in us:
        insert_search(db, i)

def _printAllData(db :Session):
    query = db.query(dbm.AddFlight).all()
    if not query:
        return
    
    df = pd.DataFrame([{
        "id": flight.id,
        "time_stamp": flight.time_stamp,
        "departure_airport": flight.departure_airport,
        "arrival_airport": flight.arrival_airport,
        "requested_date": flight.requested_date,
        "target_price": flight.target_price, 
        "more_criteria": flight.more_criteria
    } for flight in query])
    print(df)
    
#endregion

def insert_search(db: Session, flight: schemas.Flight):
    flight_to_add = dbm.UserGotFlight(
        departure_airport=flight.departure_airport,
        arrival_airport=flight.arrival_airport,
        requested_date=flight.requested_date,
        target_price=flight.best_found.price,
        more_criteria=flight.more_criteria
    )

    db.add(flight_to_add)
    db.commit()

def insert_update(db: Session, flight: schemas.Flight):
    flight_to_add = dbm.UpdateFlight(
        departure_airport=flight.departure_airport,
        arrival_airport=flight.arrival_airport,
        requested_date=flight.requested_date,
        target_price=flight.best_found.price,
        more_criteria=flight.more_criteria
    )

    db.add(flight_to_add)
    db.commit()

def user_got_his_flight(db: Session, flight: schemas.Flight):
    flight_to_add = dbm.UserGotFlight(
        departure_airport=flight.departure_airport,
        arrival_airport=flight.arrival_airport,
        requested_date=flight.requested_date,
        target_price=flight.best_found.price,
        more_criteria=flight.more_criteria
    )
    
    db.add(flight_to_add)
    db.commit()

def user_flight_expired(db: Session, flight: schemas.Flight):
    flight_to_add = dbm.UserFlightExpired(
        departure_airport=flight.departure_airport,
        arrival_airport=flight.arrival_airport,
        requested_date=flight.requested_date,
        target_price=flight.target_price,
        more_criteria=flight.more_criteria, 
        best_found=flight.best_found.to_dict() if flight.best_found else {}
    )
    
    db.add(flight_to_add)
    db.commit()