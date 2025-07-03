from fastapi import FastAPI, Request, HTTPException, status, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
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
from typing import Literal
import re
import jwt
from datetime import datetime, timedelta, timezone

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

#health checker
@app.get("/health", summary="Health Check",
         response_description="Service status",
         tags=["Monitoring"],
         responses={
             200: {"description": "Service is healthy"},
             503: {"description": "Service unavailable"}})
async def health_check():
    try:
        db.callFuncFromOtherThread() #it will open the data base and close it 
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"API Unavailable: {e}")
    
    if amadeus_api.check_health(): #check the amadeus
        return {"status": "ok", "database": "connected", "amadeus_api": "ok"} #if ok
    else:
        logger.error(f"Health check failed: on amadeus api")
        raise HTTPException(status_code=503, detail=f"Amadeus API service Unavailable")

# gives the user an error
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Too many requests, please slow down."})

#region users

#a debug func

"""
@app.get("/get_all_users", summary="Get list of all registered users",
    description="Retrieves a list of all users in the system with their basic information.",
    response_description="List of user objects",
    tags=["Users"],
    responses={
        status.HTTP_200_OK: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "content": [
                            {"id": 1, "email": "user1@example.com"},
                            {"id": 2, "email": "user2@example.com"}
                        ]
                    }
                }
            }
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Rate limit exceeded (2 requests per minute)"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Database error occurred",
            "content": {
                "application/json": {
                    "example": {"detail": "Problem with the data base. <ErrorType> - <ErrorMessage>"}
                }
            }
        }
    }
)
@limiter.limit("2/minute")  # 2 requests in a minute for every ip
async def get_all_users(request: Request, token):
    try:
        logger.info("All users list was sended")
        return JSONResponse(status_code=200, content={"status":"ok", "content" :db.callFuncFromOtherThread(db.get_all_users)})
    except HTTPException as e:
        logger.error(f"Error in /get_all_users: {e}")
        raise HTTPException(status_code=500, detail=f"Problem with the data base. {type(e)} - {e}")
"""

#region tokens and passwords

ACCESS_TOKEN_EXPIRE_MINUTES = 30
ALGORITHM = "HS256"
SECRET_KEY = os.getenv("TOKEN_SECRET_KEY")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def check_if_password_is_good(password: str) -> bool:
    """
        The password needs to be between 8-16 chars, with letters and numbers without special chars
    """
    if len(password) < 8 or len(password) > 16: return False

    hasLetters = bool(re.search(r'[a-zA-Z]', password))
    hasNumbers = bool(re.search(r'\d', password))
    if not (hasNumbers and hasLetters): return False

    if bool(re.search(r'[^a-zA-Z0-9]', password)): return False #has special chars

    return True
    
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_user_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire}) # expire date
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")

def get_current_user_id(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_access_token(token)
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
        return user_id
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Could not validate credentials: {e}")

def check_if_mail_matches_user_id(email: str, user_id:int) -> bool:
    if db.callFuncFromOtherThread(db.get_user_id_by_email, email) == user_id and user_id is not None:
        return True
    return False

#endregion

@app.post("/register_user",
    summary="Register a new user",
    description="Registers a new user in the system with the provided details.",
    response_description="Confirmation message",
    tags=["Users"],
    responses={
        status.HTTP_200_OK: {
            "application/json": {
                "example": {"message": "User added successfully", "user_email": "user@example.com"}
            }
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error or user already exists",
            "content": {
                "application/json": {
                    "examples": {
                        "Existing user": {
                            "value": {"detail": "User user@example.com already exists"}
                        },
                        "Validation error": {
                            "value": {"detail": [{"loc": ["email"], "msg": "value is not a valid email address", "type": "value_error"}]}
                        }
                    }
                }
            }
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Rate limit exceeded (3 requests per minute)"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Error in adding user: <error details>"}
                }
            }
        }
    })
@limiter.limit("3/minute")  # 3 requests in a minute for every ip
async def register_user(request: Request):
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")

        #check if the password is ok the password isnt hashed yet
        if not check_if_password_is_good(password):
            logger.warning(f"Password not good")
            raise HTTPException(status_code=422, detail=f"Password not good")

        #hash the password
        user = models.UserInfo(email=email, hash_password=hash_password(password))

        #check if the user already exists
        if db.callFuncFromOtherThread(db.get_user_id_by_email, user.email) != None:
            logger.warning(f"User already exists: {user.email}")
            raise HTTPException(status_code=422, detail=f"User {user.email} already exists")
        
        success = db.callFuncFromOtherThread(db.addUser, user)

        if success:
            logger.info(f"User added successfully: {body}")
            return JSONResponse(status_code=200, content={"message" : config.USER_ADDED_SUCCESSFULLY, "user_mail": user.email})
        else:
            logger.warning(f"warrning in /add_user {body} didnt work")
            raise HTTPException(status_code=500, detail=config.USER_ADD_FAILED)
    
    except HTTPException as e:
        raise e
    
    except ValidationError as e: #if there is a problem with the keys
        logger.warning(f"Problem with keys in add user: {body}")
        raise HTTPException(status_code=422, detail=e.errors())
        
    except Exception as e:
        #for other errors
        logger.error(f"Error in /add_user: {e}" + (f", body: {body}" if 'body' in locals() else ""))
        raise HTTPException(status_code=500, detail=f"Error in adding user: {e}")

@app.post("/login", response_model=dict)
@limiter.limit("20/minute")  # 20 requests in a minute for every ip
async def login(request: Request):
    try:
        body = await request.json()
        #user = models.UserInfo(**body)
        email = body.get("email")
        password = body.get("password")

        #check if the user exists
        if db.callFuncFromOtherThread(db.get_user_id_by_email, email) == None:
            logger.warning(f"User not exists: {email}")
            raise HTTPException(status_code=400, detail=f"User {email} not exists")
        
        #check if the password is correct the password now in the user isnt hashed
        hashed = db.callFuncFromOtherThread(db.get_user_hashed_password_by_email, email)
        if check_user_password(password, hashed):
            #login the user
            access_token_data = {"sub": str(db.callFuncFromOtherThread(db.get_user_id_by_email, email))} #the token conatines the user id
            access_token = create_access_token(access_token_data)
            return {"access_token": access_token, "token_type": "bearer"}
        else:
            logger.warning(f"Password wrong: mail - {email} password - {hashed}")
            raise HTTPException(status_code=400, detail=f"Incorrect username or password")
        
    except ValidationError as e: #if there is a problem with the keys
        logger.warning(f"Problem with keys in add user: {body}")
        raise HTTPException(status_code=422, detail=e.errors())
        
@app.delete("/del_user_by_email",
    response_model=Literal[config.USER_DELETED_SUCCESSFULLY],
    summary="Delete user by email",
    description="Removes a user account from the system using their email address.",
    tags=["Users"],
    responses={
        status.HTTP_200_OK: {
            "description": "User successfully deleted",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User deleted successfully",
                        "email": "user@example.com"
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid email format",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid email format"
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User not found"
                    }
                }
            }
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Rate limit exceeded (3 requests per minute)"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Failed to delete user"
                    }
                }
            }
        }
    })
@limiter.limit("3/minute")  # 3 requests in a minute for every ip
def delete_user(request: Request, user_email: str = Query(...), current_user_id: int = Depends(get_current_user_id)):
    
    if not check_if_mail_matches_user_id(user_email, current_user_id): #if someone else trys to delete a user that isnt him
        logger.warning(f"A user {user_email} tryes to delete other user {current_user_id}")
        raise HTTPException(status_code=403, detail="You are not authorized to add flights to other users.")

    success = db.callFuncFromOtherThread(db.delete_user, user_email)

    #return {"message": f"{config.USER_DELETED_SUCCESSFULLY if success else config.USER_DELETE_FAILED}"}
    if success:
        logger.info(f"User deleted successfully: email - {user_email}")
        return JSONResponse(status_code=200, content={"message" : config.USER_DELETED_SUCCESSFULLY, "email":user_email})
    else:
        logger.warning(f"warning in /delete_user email: {user_email}")
        raise HTTPException(status_code=500, detail=config.USER_DELETE_FAILED)

#endregion

#region flights

def check_date_format_and_past(date_str: str, fmt=config.DATE_FORMAT):
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

@app.post("/add_flight",
    summary="Add a new flight to tracking",
    description="Adds a new flight to the user's tracked flights list with price alert functionality.",
    response_description="Flight tracking confirmation",
    tags=["Flights"],
    responses={
        status.HTTP_200_OK: {
            "description": "Flight successfully added to tracking",
            "content": {
                "application/json": {
                    "example": {"message": "Flight added to tracking successfully"}
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid flight data",
            "content": {
                "application/json": {
                    "examples": {
                        "Same airports": {
                            "value": {"detail": "Departure and arrival airports cannot be the same"}
                        },
                        "Invalid date": {
                            "value": {"detail": "Requested date cannot be in the past"}
                        }
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {"detail": "User not found"}
                }
            }
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "requested_date"],
                                "msg": "invalid date format",
                                "type": "value_error.date"
                            }
                        ]
                    }
                }
            }
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Rate limit exceeded (10 requests per minute)"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to add flight to tracking"}
                }
            }
        }
    }
)
@limiter.limit("10/minute")  # 10 requests in a minute for every ip
async def add_flight(request: Request, current_user_id: int = Depends(get_current_user_id)):
    """
    Track a new flight with price alert functionality.
    
    Adds a flight route to the user's tracking list with options for price alerts.
    Validates flight data before adding to the system.
    
    Rate limited to 10 requests per minute per IP.
    
    Request Body:
        - user_id: int (required)
        - departure_airport: str (3-letter code, required)
        - arrival_airport: str (3-letter code, required)
        - requested_date: str (YYYY-MM-DD format, required)
        - target_price: float (required)
        - notify_on_any_drop: bool (optional)
    
    Returns:
        Dict: Confirmation message
    
    Raises:
        HTTPException: Various error conditions with appropriate status codes
    """
    try:
        body = await request.json()

        flight = models.Flight(**body)
        check_flight(flight)

        #check if the flight id matches the token id
        if flight.user_id != current_user_id:
            logger.warning(f"A user {flight.user_id} tryes to access other user {current_user_id} flights")
            raise HTTPException(status_code=403, detail="You are not authorized to add flights to other users.")
        
        success = db.callFuncFromOtherThread(db.addTrackedFlight, flight.user_id, flight)

        if success:
            logger.info(f"Flight added successfully: {body}")
            return JSONResponse(status_code=200, content={"message" : config.FLIGHT_ADDED_SUCCESSFULLY})
        else:
            logger.warning(f"warning in /add_flight body:{body}")
            raise HTTPException(status_code=500, detail=config.FLIGHT_ADD_FAILED)
    
    except (HTTPException, ValidationError) as e:
        # lets my errors to continue
        raise e
    except ValueError:
        logger.warning(f"Warning in /add_flight user_id: {flight.user_id} not found")
        raise HTTPException(status_code=404, detail=config.USER_NOT_FOUND_ERROR)
    except Exception as e:
        #for other errors
        logger.error(f"Error in /add_flight: {e}"+ (f", body: {body}" if 'body' in locals() else ""))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/get_flights",
    summary="Get user's tracked flights",
    description="Retrieves all flights being tracked by a specific user.",
    response_description="List of tracked flights with details",
    tags=["Flights"],
    responses={
        status.HTTP_200_OK: {
            "application/json": {
                "example": [{
                    "flight_id": 1,
                    "departure_airport": "TLV",
                    "arrival_airport": "JFK",
                    "requested_date": "2023-12-15",
                    "target_price": 500.0,
                    "last_checked": "2023-11-01T10:30:00",
                    "last_price_found": 450.0,
                    "notify_on_any_drop": True,
                    "best_price": 420.0,
                    "best_time": "Morning flight",
                    "best_airline": "Delta"
                }]
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {"detail": config.USER_NOT_FOUND_ERROR}
                }
            }
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Rate limit exceeded (10 requests per minute)"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Database error",
            "content": {
                "application/json": {
                    "example": {"detail": "Problem with the database: <error details>"}
                }
            }
        }
    }
)  # 10 requests in a minute for every ip
@limiter.limit("10/minute")
async def get_flights(request: Request, user_email: str = Query(...), current_user_id: int = Depends(get_current_user_id)):
    if not check_if_mail_matches_user_id(user_email, current_user_id):
        logger.warning(f"A user {user_email} tryes to access other user {current_user_id} flights")
        raise HTTPException(status_code=403, detail="You are not authorized to get flights from other users.")
    try:
        return JSONResponse(status_code=200, content={"flights" : db.callFuncFromOtherThread(db.getAllUserFlights, user_email)})
    except Exception as e:
        if config.USER_NOT_FOUND_ERROR in str(e): #user not found
            logger.warning(f"warning in /get_flights: user {user_email} not found")
            raise HTTPException(status_code=404, detail=config.USER_NOT_FOUND_ERROR)
        
        #a real error
        logger.error(f"Error in /get_flights: {e} email: {user_email}")
        raise HTTPException(status_code=500, detail=f"Problem with the data base. {type(e)} - {e}")

@app.delete("/del_flights",
    response_model=Literal[config.FLIGHT_DELETED_SUCCESSFULLY],
    summary="Delete a tracked flight",
    description="Removes a flight from the user's tracking list by its ID.",
    tags=["Flight Tracking"],
    responses={
        status.HTTP_200_OK: {
            "description": "Flight successfully removed from tracking",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Flight tracking deleted successfully",
                        "flight_id": 123.0
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid flight ID format",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Flight ID must be a positive number"
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Flight not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Flight not found with ID: 123.0"
                    }
                }
            }
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Rate limit exceeded (30 requests per minute)"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Database error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Failed to delete flight tracking"
                    }
                }
            }
        }
    }
    )
@limiter.limit("30/minute")  # 30 requests in a minute for every ip
async def delete_flight(request: Request, flight_id: int = Query(...), current_user_id: int = Depends(get_current_user_id)):
    
    user_id = db.callFuncFromOtherThread(db.get_user_id_by_flight_id, flight_id)
    #check if user id and token id matches
    if user_id != current_user_id:
        logger.warning(f"A user {user_id} tryes to access other user {current_user_id} flights")
        raise HTTPException(status_code=403, detail="You are not authorized to delete flights that belongs other users.")
    
    success = db.callFuncFromOtherThread(db.deleteFlightById, int(flight_id))
    if success:
        logger.info(f"Flight deleted successfully: flight_id - {flight_id}")
        return JSONResponse(status_code=200, content={"message" : config.FLIGHT_DELETED_SUCCESSFULLY, "flight_id": flight_id})
    else:
        logger.warning(f"Warning in /delete_flights flight_id: {flight_id}")
        raise HTTPException(status_code=500, detail=config.FLIGHT_DELETE_FAILED)

@app.put("/update_flight",
    response_model=Literal[config.FLIGHT_UPDATED_SUCCESSFULLY],
    summary="Update flight tracking details",
    description="Updates the tracking parameters for a specific flight.",
    tags=["Flight Tracking"],
    responses={
        status.HTTP_200_OK: {
            "description": "Flight tracking successfully updated",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Flight tracking updated successfully",
                        "flight_id": 123
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid request data",
            "content": {
                "application/json": {
                    "examples": {
                        "Same airports": {
                            "value": {"detail": "Departure and arrival airports cannot be the same"}
                        },
                        "Invalid date": {
                            "value": {"detail": "Requested date cannot be in the past"}
                        }
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "User or flight not found",
            "content": {
                "application/json": {
                    "example": {"detail": "User not found"}
                }
            }
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Rate limit exceeded (10 requests per minute)"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to update flight tracking"}
                }
            }
        }
    }
)
@limiter.limit("10/minute")  # 10 requests in a minute for every ip
async def update_flight(request: Request, current_user_id: int = Depends(get_current_user_id)) -> str:
    try:
        body = await request.json()
        flight = models.Flight(**body)

        #check if user id and token id matches
        if flight.user_id != current_user_id:
            logger.warning(f"A user {flight.user_id} tryes to access other user {current_user_id} flights")
            raise HTTPException(status_code=403, detail="You are not authorized to delete flights that belongs other users.")
    
        check_flight(flight)
        success = db.callFuncFromOtherThread(db.updateTrackedFlightDetail, flight.flight_id, flight)
        if success:
            logger.info(f"Flight updated successfully: {body}")
            return JSONResponse(status_code=200, content={"message" :config.FLIGHT_UPDATED_SUCCESSFULLY, "flight_id" : flight.flight_id})
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
    
@app.get("/get_flights_options",
    summary="Get the flight options",
    description="Get the flight options between origin and destination.",
    tags=["Flight options"],
    responses={
        status.HTTP_200_OK: {
            "description": "Flight options",
            "content": {
                "application/json": {
                        "...a lot of params"
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid request data",
            "content": {
                "application/json": {
                    "examples": {
                        "Same airports": {
                            "value": {"detail": "Departure and arrival airports cannot be the same"}
                        },
                        "Invalid date": {
                            "value": {"detail": "Requested date cannot be in the past"}
                        }
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Flight options not found",
            "content": {
                "flight options not found..."
            }
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Rate limit exceeded (10 requests per minute)"
        },
    }
)
@limiter.limit("5/minute")  # 5 requests in a minute for every ip
async def getFlightOptions(request: Request, flight: models.Flight, current_user_id: int = Depends(get_current_user_id)):
    """
    returns the flight options and None if a problem occurd
    """
    try:
        result = amadeus_api.search_flights(flight)

        flight_options = result.get("data", [])
        return flight_options

    except Exception as e:
        logger.error(f"problom in getting flights {flight.departure_airport} -> {flight.arrival_airport}: {e}")
        raise HTTPException(404, f"Flight options not found in {flight.requested_date} between {flight.departure_airport} -> {flight.arrival_airport}")
    
#endregion