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
    with open("airports_dict.json") as f:
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

#region users

@app.get("/get_all_users")
def get_all_users():
    try:
        return db.callFuncFromOtherThread(db.get_all_users)
    except Exception as e:
        logger.error(f"Error in /get_all_users: {e}")
        raise HTTPException(status_code=500, detail=f"Problem with the data base. {type(e)} - {e}")

@app.post("/add_user")
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
def delete_user(user_email: str = Query(...)):
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
        date = datetime.strptime(date_str, fmt)
    except ValueError:
        # הפורמט לא תקין
        return False, None
    
    # הפורמט תקין, בודקים אם התאריך עבר
    is_past = date < datetime.now()
    return True, is_past

def check_flight(flight : models.Flight):
    if flight.departure_airport == flight.arrival_airport:
        raise ValidationError("The departure airport and the arrival airport cant be the same")
    if flight.departure_airport not in airports:
        raise ValidationError(f"The departure airport {flight.departure_airport} isnt a supported airport")
    if flight.arrival_airport not in airports:
        raise ValidationError(f"The arrival airport {flight.departure_airport} isnt a supported airport")
    
    try:
        db.callFuncFromOtherThread(db.get_user_email_by_id, flight.user_id)
    except ValueError: #user not finded
        raise ValidationError(f"User id{flight.user_id} not found")
    
    isInFormat, isInPast =  check_date_format_and_past(flight.requested_date)
    if not isInFormat: raise ValidationError(f"The requested date {flight.requested_date} isnt in the write format - {DATE_FORMAT}")
    if isInPast: raise ValidationError(f"The requested date {flight.requested_date} cannt be in the past")

@app.post("/add_flight")
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
def get_flights(user_email: str = Query(...)):
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
async def delete_flight(flight_id: float = Query(...)):
    success = db.callFuncFromOtherThread(db.deleteFlightById, float(flight_id))
    if success:
        logger.info(f"Flight deleted successfully: flight_id - {flight_id}")
        return config.FLIGHT_DELETED_SUCCESSFULLY
    else:
        logger.warning(f"Warning in /delete_flights flight_id: {flight_id}")
        raise HTTPException(status_code=500, detail=config.FLIGHT_DELETE_FAILED)

@app.put("/update_flight")
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
    
#endregion
