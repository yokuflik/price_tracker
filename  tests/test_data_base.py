import sys
import os
import pytest
from fastapi import HTTPException

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

import CRUD_users_and_flights_data_base as control_db
from connect_to_data_base import get_db

import schemas

email = "dae@gmail.com"
hashed = "hashed"
db = next(get_db())

def test_add_update_flight():

    control_db.create_new_user(db, schemas.UserCreate(email=email, hashed_password=hashed))
    user_id = control_db.get_user_by_email(db, email).id
    flight = schemas.Flight(user_id=user_id, departure_airport="BKK", arrival_airport="CNG", requested_date="2025-07-10", target_price=500)
    
    control_db.add_flight(db, flight)
    
    #test get user flights
    user_flights = control_db.get_all_user_flights(db = db, user_email = email)
    assert len(user_flights) == 1

    #test update
    flight.target_price = 400
    flight.flight_id = user_flights[0]["flight_id"]
    control_db.update_flight(db, flight.user_id, flight)

    #test delete
    control_db.delete_flight_by_id(db, flight.flight_id)
    
def test_get_user_info():
    user_id = control_db.get_user_by_email(db, email).id
    user_email = control_db.get_user_by_id(db, user_id)

    assert user_email == email

def test_delete_user():
    control_db.delete_user(db = db, email = email, password_hash = hashed)

