from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
import dataBaseFile as db

app = FastAPI()

# מאפשר קריאות ממקומות אחרים (כמו דפדפן, Postman וכו')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/track")
async def add_flight(request: Request):
    try:
        body = await request.json()
        ip = request.client.host

        # Validate required fields
        for key in ["from", "to", "date", "target_price"]:
            if key not in body:
                raise HTTPException(status_code=400, detail=f"Missing field: {key}")

        flight = db.Flight(
            ip=ip,
            departure_airport=body["from"],
            arrival_airport=body["to"],
            requested_date=body["date"],
            target_price=float(body["target_price"])
        )

        success = db.addTrackedFlight(flight)
        #if not success:
         
        #   raise HTTPException(status_code=400, detail="Flight already tracked or user not found")
        return {"message": f"{"Flight added successfully" if success else "Failed to add flight"}"}
    except Exception as e:
        print(f"Error in /track: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/getflights")
def get_flights(ip: str = Query(...)):
    #ip = request.client.host
    try:
        #return db.getAllUserFlights(ip)
        res = db.callFuncFromOtherThread(db.getAllUserFlights, ip)

        print (res)
        return res
    except Exception as e:
        return f"Problem with the data base. {type(e)} - {e}"

"""@app.delete("/flights")
async def delete_flight(request: Request):
    body = await request.json()
    ip = request.client.host
    success = db.deleteUserFlight(ip, body["from"], body["to"], body["date"])
    if not success:
        raise HTTPException(status_code=404, detail="Flight not found")
    return {"message": "Flight deleted"}
"""