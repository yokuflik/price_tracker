import os
import sys
from datetime import datetime
import pytest
from fastapi import HTTPException
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

import myFlightsApi as api
import CRUD_users_and_flights_data_base as control_db
from connect_to_data_base import get_db

import schemas

import config

db = next(get_db())

def test_flight_check():
    now = str(datetime.now().date().strftime(config.DATE_FORMAT))
    user_id = control_db._get_all_users(db)[0].id

    flight = schemas.Flight(user_id=user_id, departure_airport="BKK", arrival_airport="CNG", requested_date=now, target_price=500)
    api.check_flight(flight)

    with pytest.raises(ValueError): #supposed to fall
        flight.departure_airport = "fsdfswg"
        api.check_flight(flight)

    with pytest.raises(ValueError): #supposed to fall
        flight.arrival_airport = flight.departure_airport
        flight.departure_airport = "BKK"
        api.check_flight(flight)

    with pytest.raises(ValueError): #supposed to fall
        flight.arrival_airport = "BKK"
        api.check_flight(flight)

    with pytest.raises(ValueError): #supposed to fall
        flight.arrival_airport = "CNG"
    
        flight.requested_date = "2015-03-30"
        api.check_flight(flight)

    with pytest.raises(ValueError): #supposed to fall
        flight.requested_date = "2015/03/30"
        api.check_flight(flight)


test_flight_check()