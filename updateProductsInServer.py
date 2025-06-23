import dataBaseFile as db
import amadeus_api
from datetime import datetime

def updateAllFlightPrices():
    db.update_all_flight_details(updateFlight)

def updateFlight(flight: db.Flight):
    #print_flight_options(getFlightDetails(flight))
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

    print (bestPrice)
    if bestPrice < float(flight.last_checked_price): #new best price
        flight.last_checked_price = bestPrice

    return flight
    
def getFlightOptions(flight: db.Flight):
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

def main():
    updateAllFlightPrices()
    #print(db.getAllUsers())

if __name__ == "__main__":
    main()
