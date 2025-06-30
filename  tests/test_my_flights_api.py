import os
import sys
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

import models
import dataBaseFile as db
import myFlightsApi as api

def test_flight_check():
    now = str(datetime.now().date().strftime(api.DATE_FORMAT))
    user_id = db.callFuncFromOtherThread(db.get_all_users)[0]["id"]

    flight = models.Flight(user_id=user_id, departure_airport="BKK", arrival_airport="CNG", requested_date=now, target_price=500)
    try:
        api.check_flight(flight)
    except Exception as e:
        print (f"\n\nerror: {e}\n\n")
        assert False

    try: #supposed to fall
        flight.departure_airport = "fsdfswg"
        api.check_flight(flight)
        assert False
    except:
        pass
    try:  #supposed to fall
        flight.arrival_airport = flight.departure_airport
        flight.departure_airport = "BKK"
        api.check_flight(flight)
        assert False
    except:
        pass

    try: #supposed to fall
        flight.arrival_airport = "BKK"
        api.check_flight(flight)
        assert False
    except:
        pass

    flight.arrival_airport = "CNG"
    
    try:
        flight.requested_date = "2015-03-30"
        api.check_flight(flight)
        flight.requested_date = "2015/03/30"
        api.check_flight(flight)
        assert False
    except:
        pass
