
import os
import requests
from dotenv import load_dotenv

load_dotenv()


AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")
TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
FLIGHT_SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

def get_access_token():
    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_API_KEY,
        "client_secret": AMADEUS_API_SECRET
    }
    response = requests.post(TOKEN_URL, data=data)
    response.raise_for_status()
    token = response.json().get("access_token")
    return token

def search_flights(origin, destination, departureDate):
    token = get_access_token()
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
    response = requests.get(FLIGHT_SEARCH_URL, headers=headers, params=params)
    response.raise_for_status()
    return response.json()