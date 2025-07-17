import os
import requests
from dotenv import load_dotenv
from cachetools import TTLCache
import config
import logging
import time
from datetime import datetime, timedelta
import schemas
import json
import amadeus_history_data_base as history_db
from config import settings

# Using TTLCache instead of a regular dictionary for practice.
# For this scale (up to ~50,000 entries), a simple in-memory dict would be more efficient,
# but TTLCache gives built-in expiration which is useful for production-like scenarios.
cache = TTLCache(maxsize=50000, ttl=3600)

def get_cache_key(origin, destination, departureDate):
    return f"{origin}|{destination}|{departureDate}"

#region logger

#set the logger

LOGGER_NAME = "amadeus_api_logger.log"

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(f"{settings.LOGGOR_FOLDER_PATH}/{LOGGER_NAME}", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

#endregion

def check_health() -> bool:
    """
    checks if the amadeus api is working good
    """
    try:
        token = _get_access_token()

        #save the token to the cache
        token_cache["token"] = token

        return True
    except Exception as e:
        logger.error(f"Error in checking Amadeus API health: {e}")
        # If there's an error, we assume the API is not healthy.
        return False

token_cache = TTLCache(maxsize=1, ttl=3600)

lastTokenTime = 0
def _get_access_token():
    """
    gets the token to access the amadeus api
    """
    try:
        data = {
            "grant_type": "client_credentials",
            "client_id": settings.AMADEUS_API_KEY,
            "client_secret": settings.AMADEUS_API_SECRET
        }
        response = requests.post(settings.TOKEN_URL, data=data, timeout=20)
        response.raise_for_status()
        token = response.json().get("access_token")

        global lastTokenTime
        lastTokenTime = time.time()

        logger.info(f"Token taken at {datetime.now()}")

        return token
    except requests.RequestException:
        return None

def search_flights(flight: schemas.Flight, filter: bool = True, flights_list = None) -> list[dict]:
    """
    search the flight options from the amadeus api for the number fo days the user wants to get flight offers from 
    and filter them if filter = True by max connection number and max connection hours
    """

    if flights_list == None: #you can give a flight_list for mock data
        flights_list = [] #list(list(dict))
        if flight.more_criteria.flexible_days_before == 0 and flight.more_criteria.flexible_days_after == 0:
            flights_list.append(search_flights_for_specific_day(flight)) #append list(dict)
        else:
            #calculate the days number and the start day date
            days = flight.more_criteria.flexible_days_before + 1 + flight.more_criteria.flexible_days_after
            start_day = datetime.strptime(flight.requested_date, config.DATE_FORMAT) #set the date in a date format
            start_day = start_day - timedelta(days=flight.more_criteria.flexible_days_before)
                                              
            original_requsted_date = flight.requested_date

            #get the flight offers for every day in the dates the user wants to
            for i in range(days):
                cur_day_date = start_day + timedelta(days=i)
                flight.requested_date = cur_day_date.strftime(config.DATE_FORMAT)
                flights_list.append(search_flights_for_specific_day(flight)) #append list(dict)

            flight.requested_date = original_requsted_date

    res = []

    #filter the results
    if filter:
        res = filter_flights(flight, flights_list)
    else:
        for fl in flights_list: #to make it a big list from a list of lists
            res.extend(fl)

    return res

def filter_flights(flight : schemas.Flight, flights_list: list[list[dict]]) -> list[list[dict]]:
    """
    the function filter the list of flight offers by connection times and max connection hours
    """
    #filter connection numbers
    if flight.more_criteria.connection != 0:
        for curFlight in flights_list:
            data_dict = json.loads(curFlight)
            flight_offers_data = data_dict.get("data", [])
            classified_flights = set_flights_by_connection_numbers(flight_offers_data) #a dict with numbers of connection {0:[flight_list], 2:[flight_list]}
                
            for j in range(flight.more_criteria.connection+1):
                if j in classified_flights:
                    res = res + classified_flights[j] #leaves in the list only the flights with the number of connection or less wanted

        #filter max connection hours
        res = filter_flight_connection_hours(res, flight.more_criteria.max_connection_hours)

        return res
    else:
        return flights_list

def search_flights_for_specific_day(flight: schemas.Flight) -> list[dict]:
    """
    get all the flight options for a specific date from amadeus api
    """
    #check if the flight search is in the cache
    key = get_cache_key(flight.departure_airport, flight.arrival_airport, flight.requested_date)
    if key in cache:
        return cache[key]
    
    #use the last token if its still valid
    if "token" in token_cache:
        token = token_cache["token"]
        try_last_token = True
    else:
        token = _get_access_token()
        try_last_token = False
        token_cache["token"] = token

    if token == None: return [{"error" : config.TOKEN_ERROR}]
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    params = {
        "originLocationCode": flight.departure_airport,
        "destinationLocationCode": flight.arrival_airport,
        "departureDate": flight.requested_date,
        "adults": 1, # Keeping 1 as requested by the user
        "max": 5 #can be more in production version its like this because costs
    }

    #get the flights from the amadeus api
    try:
        response = requests.get(settings.FLIGHT_SEARCH_URL, headers=headers, params=params, timeout=20)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401 and try_last_token:
            #the token isnt good
            del token_cache["token"]

            global lastTokenTime
            logger.info(f"Token deleted after {time.time() - lastTokenTime} seconds")
            lastTokenTime = 0

            #call the func again
            return search_flights(flight, filter)
        else:
            logger.error(f"Errer in searching {e}")
            raise e
            
    res = response.json()
    cache[key] = res #add the result to the cache

    #add to history db
    history_db.insert_search(flight)

    logger.info (f"Flight search at {datetime.now()} from {flight.departure_airport} to {flight.arrival_airport} in {flight.requested_date}") #add the search to the logger
    return res

def set_flights_by_connection_numbers(flight_ofers: list[dict]) -> dict[int, list[dict]]:
    """
    set the flights in a dict that the keys are the connection number - {1:[ { flight1 }, { flight2 }], 2: [ { flight3 }, { flight4 } ]}
    """
    
    # Initialize flights_by_connections as a dictionary with lists for each category
    flights_by_connections = {}

    for offer in flight_ofers:
        if "itineraries" in offer and offer["itineraries"]:
            itinerary = offer["itineraries"][0]
            segments = itinerary.get("segments", [])

            num_connections = len(segments) - 1 # It's a list of segments of the way

            # Categorize the flight
            if num_connections not in flights_by_connections:
                flights_by_connections[num_connections] = []
                
            flights_by_connections[num_connections].append(offer)
            
    return flights_by_connections

def filter_flight_connection_hours(flight_ofers: list[dict], max_connection_hours: float) -> list[dict]:
    res = []
    for offer in flight_ofers:
        connection_times = calculate_connection_hours(offer["itineraries"][0]) # send him the segments
        if max(connection_times) <= max_connection_hours: #a good offer
            res.append(offer)

        #if the max connection hour is bigger then the max possible it will be filtered
    
    return res

def calculate_connection_hours(itinerary: dict) -> list[float]:
    """
    calculate how much hours is between the connections
    """
    
    connection_times_hours = []
    segments = itinerary.get("segments", [])

    if len(segments) < 2:
        return []

    for i in range(len(segments) - 1):
        current_segment_arrival_time_str = segments[i]['arrival']['at']
        
        next_segment_departure_time_str = segments[i+1]['departure']['at']

        arrival_dt = datetime.fromisoformat(current_segment_arrival_time_str)
        departure_dt = datetime.fromisoformat(next_segment_departure_time_str)

        connection_duration = departure_dt - arrival_dt

        connection_hours = connection_duration.total_seconds() / 3600
        connection_times_hours.append(connection_hours)

    return connection_times_hours
