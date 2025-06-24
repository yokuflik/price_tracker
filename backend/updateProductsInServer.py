import dataBaseFile as db
import amadeus_api
from datetime import datetime
import models

def updateAllFlightPrices():
    db.callFuncFromOtherThread(db.update_all_flight_details, updateBestFlight)
    print (db.callFuncFromOtherThread(db.getAllUsers))

def updateBestFlight(flight: models.Flight):
    #find the best flight
    flightOptions = getFlightOptions(flight)
    bestPrice = None
    bestOffer = None
    for offer in flightOptions: #find the best price
        curPrice = float(offer["price"]["total"])
        if bestPrice: 
            if  curPrice< bestPrice:
                bestPrice = curPrice
                bestOffer = offer
        else: #the first offer
            bestPrice = curPrice
            bestOffer = offer

    #update the last time update and best last price
    flight.last_checked = datetime.now().strftime("%-d/%-m/%Y %H:%M")
    flight.last_checked_price = bestPrice #saves the last best offer
    if flight.best_price == None or bestPrice <= float(flight.best_price): #new best price
        #update the flight details
        flight.best_price = bestPrice
        flight.best_airline = bestOffer["validatingAirlineCodes"][0]
        departure = bestOffer["itineraries"][0]["segments"][0]["departure"]["at"]
        arrival = bestOffer["itineraries"][0]["segments"][0]["arrival"]["at"]
        flight.best_time = f'departure: {datetime.fromisoformat(departure).strftime("%-d/%-m/%Y %H:%M")}, arrival: {datetime.fromisoformat(arrival).strftime("%-d/%-m/%Y %H:%M")}'

        #only if its the first time i found it to not disturb every time
        if bestPrice <= float(flight.target_price):
            foundBetterFlight(flight)

    return flight
    
def getFlightOptions(flight: models.Flight):
    """
    returns the flight options
    """
    try:
        result = amadeus_api.search_flights(
            flight.departure_airport,
            flight.arrival_airport,
            flight.requested_date
        )

        flight_options = result.get("data", [])
        return flight_options

    except Exception as e:
        print(f"שגיאה בחיפוש טיסה {flight.departure_airport} -> {flight.arrival_airport}: {e}")
        return []

def print_flight_options(flight_options):
    """
    מדפיסה את כל האפשרויות שקיבלנו מה־API של אמדאוס.
    """
    if not flight_options:
        print("לא נמצאו טיסות מתאימות.")
        return

    for offer in flight_options:
        try:
            price = offer["price"]["total"]
            airline = offer["validatingAirlineCodes"][0]
            segments = offer["itineraries"][0]["segments"]
            departure = segments[0]["departure"]["at"]
            arrival = segments[-1]["arrival"]["at"]

            print(f"{airline} - price: {price} EUR")
            print(f"  departure: {datetime.fromisoformat(departure).strftime("%-d/%-m/%Y %H:%M")}")
            print(f"  arrival: {datetime.fromisoformat(arrival).strftime("%-d/%-m/%Y %H:%M")}")
            print("-" * 30)
        except Exception as e:
            print(f"Problem in the processing: {e}")

def foundBetterFlight(flight: models.Flight):
    print (f"Found better flight ")

def main():
    #while True:
    updateAllFlightPrices()
        #time.sleep(3600) #it will be activated when it will work
    #print(db.getAllUsers())

if __name__ == "__main__":
    main()