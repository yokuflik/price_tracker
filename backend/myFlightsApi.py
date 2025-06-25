from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
import dataBaseFile as db
import config
import models
import logging
import os
from dotenv import load_dotenv

#region loggs file

load_dotenv()

LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "api.log")
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
        body = await request.json()

        user = models.UserInfo.from_dict(body)
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

@app.delete("/del_user_by_ip")
def delete_user(user_ip: str = Query(...)):
    success = db.callFuncFromOtherThread(db.delete_user, user_ip)

    #return {"message": f"{config.USER_DELETED_SUCCESSFULLY if success else config.USER_DELETE_FAILED}"}
    if success:
        logger.info(f"User deleted successfully: ip - {user_ip}")
        return config.USER_DELETED_SUCCESSFULLY
    else:
        logger.warning(f"warning in /delete_user ip:{user_ip}")
        raise HTTPException(status_code=500, detail=config.USER_DELETE_FAILED)

#endregion

#region flights

@app.post("/add_flight")
async def add_flight(request: Request):
    try:
        body = await request.json()

        flight = models.Flight.from_dict(body)
        
        success = db.callFuncFromOtherThread(db.addTrackedFlight, flight)

        if success:
            logger.info(f"Flight added successfully: {body}")
            return config.FLIGHT_ADDED_SUCCESSFULLY
        else:
            logger.warning(f"warning in /add_flight body:{body}")
            raise HTTPException(status_code=500, detail=config.FLIGHT_ADD_FAILED)
        #return {"message": f"{config.FLIGHT_ADDED_SUCCESSFULLY if success else config.FLIGHT_ADD_FAILED}"}
    
    except HTTPException as e:
        # נותן לשגיאות שיצרת במכוון לעבור הלאה
        raise e
    
    except Exception as e:
        if config.USER_NOT_FOUND_ERROR in str(e): #user not found
            logger.warning(f"Warning in /add_flight ip: {flight.ip} not found")
            raise HTTPException(status_code=404, detail=config.USER_NOT_FOUND_ERROR)

        #for other errors
        logger.error(f"Error in /add_flight: {e}"+ (f", body: {body}" if 'body' in locals() else ""))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/get_flights")
def get_flights(ip: str = Query(...)):
    try:
        return db.callFuncFromOtherThread(db.getAllUserFlights, ip)
    except Exception as e:
        if config.USER_NOT_FOUND_ERROR in str(e): #user not found
            logger.warning(f"warning in /get_flights: flight {ip} not found")
            raise HTTPException(status_code=404, detail=config.USER_NOT_FOUND_ERROR)
        
        #a real error
        logger.error(f"Error in /get_flights: {e} ip: {ip}")
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
        flight_id = body.get("flight_id")
        flight = models.Flight.from_dict(body)
        print(flight_id)
        success = db.callFuncFromOtherThread(db.updateTrackedFlightDetail, flight_id, flight)
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
            logger.warning(f"Warningg in /update_flight: user ip:{flight.ip} not found")
            raise HTTPException(status_code=404, detail=config.USER_NOT_FOUND_ERROR)
        logger.error(f"Error in /update_flight: {e}"+ (f", body: {body}" if 'body' in locals() else ""))
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error in /update_flight: {e}"+ (f", body: {body}" if 'body' in locals() else ""))
        raise HTTPException(status_code=500, detail="Internal server error")
    
#endregion