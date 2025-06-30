from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
import dataBaseFile as db
import config
import models
import logging
import os
from dotenv import load_dotenv
from pydantic import ValidationError
import json
from datetime import datetime
import amadeus_api
import bcrypt

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

#region loggs file

load_dotenv()

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

#load all the airports
def getAirportsDict():
    file = os.getenv("AIRPORTS_DICT_FILE")
    with open(file) as f:
        return json.load(f)

airports = getAirportsDict()

app = FastAPI()

#its here so i can call from the web brwosher
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()

# gives the user an error
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Too many requests, please slow down."})

#region users

@app.get("/get_all_users")
@limiter.limit("2/minute")  # 2 requests in a minute for every ip
def get_all_users(request: Request):
    try:
        logger.info("All users list was sended")
        return db.callFuncFromOtherThread(db.get_all_users)
    except Exception as e:
        logger.error(f"Error in /get_all_users: {e}")
        raise HTTPException(status_code=500, detail=f"Problem with the data base. {type(e)} - {e}")

@app.post("/add_user")
@limiter.limit("3/minute")  # 3 requests in a minute for every ip
async def add_user(request: Request):
    try:
        try:
            body = await request.json()
            user = models.UserInfo(**body)

            #check if the user already exists
            if db.callFuncFromOtherThread(db.get_user_id_by_email, user.email) != None:
                logger.warning(f"User already exists: {user.email}")
                raise HTTPException(status_code=422, detail=f"User {user.email} already exists")
            
        except ValidationError as e: #if there is a problem with the keys
            logger.warning(f"Problem with keys in add user: {body}")
            raise HTTPException(status_code=422, detail=e.errors())
        
        success = db.callFuncFromOtherThread(db.addUser, user)

        if success:
            logger.info(f"User added successfully: {body}")
            return config.USER_ADDED_SUCCESSFULLY
        else:
            logger.warning(f"warrning in /add_user {body} didnt work")
            raise HTTPException(status_code=500, detail=config.USER_ADD_FAILED)
    
    except HTTPException as e:
        # נותן לשגיאות שיצרת במכוון לעבור הלאה
        raise e
    
    except Exception as e:
        #for other errors
        logger.error(f"Error in /add_user: {e}" + (f", body: {body}" if 'body' in locals() else ""))
        raise HTTPException(status_code=500, detail=f"Error in adding user: {e}")

@app.delete("/del_user_by_email")
@limiter.limit("3/minute")  # 3 requests in a minute for every ip
def delete_user(request: Request, user_email: str = Query(...)):
    success = db.callFuncFromOtherThread(db.delete_user, user_email)

    #return {"message": f"{config.USER_DELETED_SUCCESSFULLY if success else config.USER_DELETE_FAILED}"}
    if success:
        logger.info(f"User deleted successfully: email - {user_email}")
        return config.USER_DELETED_SUCCESSFULLY
    else:
        logger.warning(f"warning in /delete_user email: {user_email}")
        raise HTTPException(status_code=500, detail=config.USER_DELETE_FAILED)

#endregion

#region flights

DATE_FORMAT = "%Y-%m-%d"
def check_date_format_and_past(date_str: str, fmt=DATE_FORMAT):
    try:
        date = datetime.strptime(date_str, fmt).date()
    except ValueError:
        return False, None
    
    # הפורמט תקין, בודקים אם התאריך עבר
    is_past = date < datetime.now().date()
    return True, is_past

def check_flight(flight: models.Flight):
    if flight.departure_airport == flight.arrival_airport:
        raise ValueError("The departure airport and the arrival airport can't be the same")

    if flight.departure_airport not in airports:
        raise ValueError(f"The departure airport '{flight.departure_airport}' isn't a supported airport")

    if flight.arrival_airport not in airports:
        raise ValueError(f"The arrival airport '{flight.arrival_airport}' isn't a supported airport")
    
    try:
        db.callFuncFromOtherThread(db.get_user_email_by_id, flight.user_id)
    except ValueError:  # user not found
        raise ValueError(f"User id {flight.user_id} not found")
    
    isInFormat, isInPast = check_date_format_and_past(flight.requested_date)
    if not isInFormat:
        raise ValueError(f"The requested date '{flight.requested_date}' isn't in the right format - {DATE_FORMAT}")
    if isInPast:
        raise ValueError(f"The requested date '{flight.requested_date}' cannot be in the past")

@app.post("/add_flight")
@limiter.limit("10/minute")  # 10 requests in a minute for every ip
async def add_flight(request: Request):
    try:
        body = await request.json()

        flight = models.Flight(**body)
        check_flight(flight)

        success = db.callFuncFromOtherThread(db.addTrackedFlight, flight.user_id, flight)

        if success:
            logger.info(f"Flight added successfully: {body}")
            return config.FLIGHT_ADDED_SUCCESSFULLY
        else:
            logger.warning(f"warning in /add_flight body:{body}")
            raise HTTPException(status_code=500, detail=config.FLIGHT_ADD_FAILED)
        #return {"message": f"{config.FLIGHT_ADDED_SUCCESSFULLY if success else config.FLIGHT_ADD_FAILED}"}
    
    except (HTTPException, ValidationError) as e:
        # נותן לשגיאות שיצרת במכוון לעבור הלאה
        raise e
    
    except Exception as e:
        if config.USER_NOT_FOUND_ERROR in str(e): #user not found
            logger.warning(f"Warning in /add_flight user_id: {flight.user_id} not found")
            raise HTTPException(status_code=404, detail=config.USER_NOT_FOUND_ERROR)

        #for other errors
        logger.error(f"Error in /add_flight: {e}"+ (f", body: {body}" if 'body' in locals() else ""))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/get_flights")
@limiter.limit("10/minute")  # 10 requests in a minute for every ip
def get_flights(request: Request, user_email: str = Query(...)):
    try:
        print(user_email)
        return db.callFuncFromOtherThread(db.getAllUserFlights, user_email)
    except Exception as e:
        if config.USER_NOT_FOUND_ERROR in str(e): #user not found
            logger.warning(f"warning in /get_flights: user {user_email} not found")
            raise HTTPException(status_code=404, detail=config.USER_NOT_FOUND_ERROR)
        
        #a real error
        logger.error(f"Error in /get_flights: {e} email: {user_email}")
        raise HTTPException(status_code=500, detail=f"Problem with the data base. {type(e)} - {e}")

@app.delete("/del_flights")
@limiter.limit("30/minute")  # 30 requests in a minute for every ip
async def delete_flight(request: Request, flight_id: float = Query(...)):
    success = db.callFuncFromOtherThread(db.deleteFlightById, float(flight_id))
    if success:
        logger.info(f"Flight deleted successfully: flight_id - {flight_id}")
        return config.FLIGHT_DELETED_SUCCESSFULLY
    else:
        logger.warning(f"Warning in /delete_flights flight_id: {flight_id}")
        raise HTTPException(status_code=500, detail=config.FLIGHT_DELETE_FAILED)

@app.put("/update_flight")
@limiter.limit("10/minute")  # 10 requests in a minute for every ip
async def update_flight(request: Request):
    try:
        body = await request.json()
        flight = models.Flight(**body)
        check_flight(flight)
        success = db.callFuncFromOtherThread(db.updateTrackedFlightDetail, flight.flight_id, flight)
        if success:
            logger.info(f"Flight updated successfully: {body}")
            return config.FLIGHT_UPDATED_SUCCESSFULLY
        else:
            logger.warning(f"Warning in /update_flight"+ (f", body: {body}" if 'body' in locals() else ""))
            raise HTTPException(status_code=500, detail=config.FLIGHT_UPDATE_FAILED)
        
    except HTTPException as e:
        # let the error i ade to keep going
        raise e
    
    except ValueError as e:
        if config.USER_NOT_FOUND_ERROR in str(e):
            logger.warning(f"Warningg in /update_flight: user_id: {flight.user_id} not found")
            raise HTTPException(status_code=404, detail=config.USER_NOT_FOUND_ERROR)
        logger.error(f"Error in /update_flight: {e}"+ (f", body: {body}" if 'body' in locals() else ""))
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error in /update_flight: {e}"+ (f", body: {body}" if 'body' in locals() else ""))
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.get("/get_flights_options")
@limiter.limit("5/minute")  # 5 requests in a minute for every ip
async def getFlightOptions(request: Request, flight: models.Flight):
    """
    returns the flight options and None if a problem occurd
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
        logger.error(f"problom in getting flights {flight.departure_airport} -> {flight.arrival_airport}: {e}")
        return None
    
#endregion

#region passwords

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
plain_password = "mySuperSecret123"
hashed = hash_password(plain_password)

print("Hashed:", hashed)

# בדיקה
if check_password("mySuperSecret123", hashed):
    print("Password correct ✅")
else:
    print("Wrong password ❌")

#endregion