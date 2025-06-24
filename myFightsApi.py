from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
import dataBaseFile as db
import config

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
        return f"Problem with the data base. {type(e)} - {e}"

#endregion

#region flights

@app.post("/add_flight")
async def add_flight(request: Request):
    try:
        body = await request.json()

        flight = config.Flight.from_dict(body)
        
        success = db.callFuncFromOtherThread(db.addTrackedFlight, flight)

        return {"message": f"{"Flight added successfully" if success else "Failed to add flight"}"}
    except Exception as e:
        if config.USER_NOT_FOUND_ERROR in e: #user not found
            return config.USER_NOT_FOUND_ERROR

        #for other errors
        print(f"Error in /track: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/get_flights")
def get_flights(ip: str = Query(...)):
    #ip = request.client.host
    try:
        #return db.getAllUserFlights(ip)
        res = db.callFuncFromOtherThread(db.getAllUserFlights, ip)

        return res
    except Exception as e:
        if config.USER_NOT_FOUND_ERROR in e: #user not found
            return config.USER_NOT_FOUND_ERROR
        
        return f"Problem with the data base. {type(e)} - {e}"

@app.delete("/del_flights")
async def delete_flight(flight_id: float = Query(...)):
    success = db.callFuncFromOtherThread(db.deleteFlightById, float(flight_id))
    if not success:
        return config.FLIGHT_DELETE_FAILED
    return config.FLIGHT_DELETED_SUCCESSFULLY

#endregion