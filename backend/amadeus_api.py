import os
import requests
from dotenv import load_dotenv
from cachetools import TTLCache
import config
import logging
import time
from datetime import datetime

# Using TTLCache instead of a regular dictionary for practice.
# For this scale (up to ~50,000 entries), a simple in-memory dict would be more efficient,
# but TTLCache gives built-in expiration which is useful for production-like scenarios.
cache = TTLCache(maxsize=50000, ttl=3600)

def get_cache_key(origin, destination, departureDate):
    return f"{origin}|{destination}|{departureDate}"

load_dotenv()

#region logger

#set the logger
LOG_FILE_PATH = os.getenv("API_LOG_FILE_PATH", "api.log")
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

AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")
TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
FLIGHT_SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

def check_health() -> bool:
    #In a production virsion I will realy check but I dont want to waste the tokens
    return True

token_cache = TTLCache(maxsize=1, ttl=3600)

lastTokenTime = 0
def _get_access_token():
    try:
        data = {
            "grant_type": "client_credentials",
            "client_id": AMADEUS_API_KEY,
            "client_secret": AMADEUS_API_SECRET
        }
        response = requests.post(TOKEN_URL, data=data, timeout=20)
        response.raise_for_status()
        token = response.json().get("access_token")

        global lastTokenTime
        lastTokenTime = time.time()

        logger.info(f"Token taken at {datetime.now()}")

        return token
    except requests.RequestException:
        return None

def search_flights(origin, destination, departureDate):
    #check if is in the cache
    key = get_cache_key(origin, destination, departureDate)
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

    if token == None: return config.TOKEN_ERROR
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departureDate,
        "adults": 1,
        "max": 5
    }
    try:
        response = requests.get(FLIGHT_SEARCH_URL, headers=headers, params=params, timeout=20)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401 and try_last_token:
            #the token isnt good
            del token_cache["token"]

            global lastTokenTime
            logger.info(f"Token deleted after {time.time() - lastTokenTime} seconds")
            lastTokenTime = 0

            #call the func again
            return search_flights(origin, destination, departureDate)
        else:
            logger.error(f"Errer in searching {e}")
            raise e
            
    res = response.json()
    cache[key] = res #add the result to the cache
    logger.info (f"Flight search at {datetime.now()} from {origin} to {destination} in {departureDate}") #add the search to the logger
    return res
