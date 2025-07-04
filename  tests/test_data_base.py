import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from data_bases_code import dataBaseFile as db
import models

email = "dae@gmail.com"
def test_add_user():
    assert db.callFuncFromOtherThread(db.addUser, models.UserInfo(email=email, hash_password="hashed"))

def test_add_update_flight():
    user_id = db.callFuncFromOtherThread(db.get_user_id_by_email, email)
    flight = models.Flight(user_id=user_id, departure_airport="BKK", arrival_airport="CNG", requested_date="2025-07-01", target_price=500)

    assert db.callFuncFromOtherThread(db.addTrackedFlight, user_id, flight)

    #test get user flights
    user_flights = db.callFuncFromOtherThread(db.getAllUserFlights, email)
    assert len(user_flights) == 1

    #test update
    flight.target_price = 400
    flight.flight_id = user_flights[0]["flight_id"]
    assert db.callFuncFromOtherThread(db.updateTrackedFlightDetail, flight.flight_id, flight)

    #test delete
    assert db.callFuncFromOtherThread(db.deleteFlightById, flight.flight_id)
    
def test_get_user_info():
    user_id = db.callFuncFromOtherThread(db.get_user_id_by_email, email)
    user_email = db.callFuncFromOtherThread(db.get_user_email_by_id, int(user_id))

    assert user_email == email

def test_delete_user():
    assert db.callFuncFromOtherThread(db.delete_user, email)

