from data_bases_code import dataBaseFile as db
import amadeus_api
from datetime import datetime
import models
import os
from dotenv import load_dotenv
import requests

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from data_bases_code import user_flight_history_data_base as flight_history_db

#region logger
load_dotenv()

LOG_FILE_PATH = os.getenv("UPDATE_IN_SERVER_LOG_FILE_PATH", "update_in_server.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

#set the dir
log_dir = os.path.dirname(LOG_FILE_PATH)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

#endregion

#region email

EMAIL_ADDRESS = os.getenv("API_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(recipient_email: str, subject: str, body: str) -> bool:
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent to user {recipient_email}: {body}")
        return True

    except Exception as e:
        logger.error(f"Error in sending email to {recipient_email}")
        return False

#endregion

def updateAllFlightPrices():
    db.callFuncFromOtherThread(db.update_all_flight_details, updateBestFlight)

def updateBestFlight(flight: models.Flight) -> models.Flight:
    """
    the function that updates the flight last price found and best price found if founded and also notifys the user if found the flight he wanted
    """

    #find the best flight
    flightOptions = getFlightOptions(flight)
    bestPrice = None
    bestOffer = None

    for offer in flightOptions: #find the best price
        offer = offer.get("data", [])
        curPrice = float(offer["price"]["total"])
        if bestPrice: 
            if curPrice < bestPrice:
                bestPrice = curPrice
                bestOffer = offer
        else: #the first offer
            bestPrice = curPrice
            bestOffer = offer

    #update the last time update and best last price
    flight.last_checked = datetime.now().strftime("%-d/%-m/%Y %H:%M:%S")

    notify = False
    if flight.best_found.price is None: #the first time
        flight.best_found.price = 0
    elif float(flight.best_found.price) <= flight.target_price: #that means that i already found a flight in the target price
        notify = flight.notify_on_any_drop

    flight.last_price_found = bestPrice #saves the last best offer
    if flight.best_found.price == 0 or bestPrice < flight.best_found.price: #new best price
        #update the flight details
        flight.best_found.price = bestPrice
        flight.best_found.airline = bestOffer["validatingAirlineCodes"][0]
        departure = bestOffer["itineraries"][0]["segments"][0]["departure"]["at"]
        arrival = bestOffer["itineraries"][0]["segments"][0]["arrival"]["at"]
        flight.best_found.time = f'departure: {datetime.fromisoformat(departure).strftime("%-d/%-m/%Y %H:%M")}, arrival: {datetime.fromisoformat(arrival).strftime("%-d/%-m/%Y %H:%M")}'

        #only if its the first time I found it to not disturb every time
        if bestPrice <= flight.target_price or notify:
            foundBetterFlight(flight)

    return flight
    
def getFlightOptions(flight: models.Flight) -> list[dict]:
    """
    returns the flight options can raise an http error back
    """
    try:
        result = amadeus_api.search_flights(flight)

        #flight_options = result.get("data", [])
        return result

    except requests.exceptions.HTTPError as e:
        logger.error(f"problom in getting flights {flight.departure_airport} -> {flight.arrival_airport}: {e}")
        raise e

def _print_flight_options(flight_options):
    if not flight_options:
        print("Didnt find any flights")
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
    """
    add the flight that was founded to the correct data base and then notify the user in the production it will be by email
    """
    #add to the data base
    flight_history_db.callFuncFromOtherThread(flight_history_db.user_got_his_flight, flight)
    print("found better flight")

    #send_email(db.callFuncFromOtherThread(db.get_user_email_by_id, float(flight.user_id)), 
     #          f"Hi \nWe found a flight in the price you wanted - {flight.best_found.time} in {flight.best_found.price}$ by {flight.best_found.airline}")

def main():
    print (type(getFlightOptions(models.Flight(user_id=2, departure_airport="TLV", arrival_airport="JFK", 
                                               requested_date="2025-12-12", target_price=400))))
    #while True:
    #updateAllFlightPrices()
        #time.sleep(3600) #it will be activated when it will work

if __name__ == "__main__":
    main()