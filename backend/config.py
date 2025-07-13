#this is the flie with all the global variabels
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    AMADEUS_API_KEY: str = os.getenv("AMADEUS_API_KEY")
    AMADEUS_API_SECRET: str = os.getenv("AMADEUS_API_SECRET")
    TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
    FLIGHT_SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

    LOGGOR_FOLDER_PATH: str = os.getenv("LOG_FILE_PATH", "logs")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    if LOGGOR_FOLDER_PATH and not os.path.exists(LOGGOR_FOLDER_PATH):
        os.makedirs(LOGGOR_FOLDER_PATH)

settings = Settings()

TOKEN_ERROR = "Error with the api token"

DATE_FORMAT = "%Y-%m-%d"

USER_NOT_FOUND_ERROR = "No user found with email"
CONNECTION_PROBLEM = "Problem with the connection"

USER_ADDED_SUCCESSFULLY = "The user was added"
USER_ADD_FAILED = "The user add failed"

USER_DELETED_SUCCESSFULLY = "The user was deleted"
USER_DELETE_FAILED = "The user delete failed"

FLIGHT_ADDED_SUCCESSFULLY = "The flight was added"
FLIGHT_ADD_FAILED = "The flight add failed"

FLIGHT_DELETED_SUCCESSFULLY = "The flight was deleted"
FLIGHT_DELETE_FAILED = "The flight delete failed"

FLIGHT_UPDATED_SUCCESSFULLY = "The flight updated successfully"
FLIGHT_UPDATE_FAILED = "Flight update failed"
