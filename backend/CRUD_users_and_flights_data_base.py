from sqlite3 import IntegrityError
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from fastapi import HTTPException, status

from config import settings
import data_base_models as dbm
import connect_to_data_base as db_connection

from datetime import datetime

import schemas

#region debug

def _get_all_users(db:Session) -> list[dbm.User]:
    return db.query(dbm.User).all()

def _create_five_dummy_users(db: Session):
    print("Creating 5 dummy users...")
    for i in range(1, 6):
        email = f"dummy_user_{i}@example.com"
        password = f"dummyPassword{i}!"
        user_data = schemas.UserCreate(email=email, hashed_password=password)

        try:
            get_user_by_email(db, email)
            print(f"  User {email} already exists. Skipping.")
        except:
            user_id = create_new_user(db, user_data)
            add_flight(db, schemas.Flight(user_id=user_id, departure_airport="TLV", arrival_airport="BKK", requested_date="2025-10-10", target_price=400))
        

def _print_all_users_and_flights(db: Session):
    users = _get_all_users(db)

    for user in users:
        print (f"{user}\n----flights----")
        flights = get_all_user_flights(db, user.id)
        if len(flights) == 0:
            print ("user dousnt have flights")
        else:
            flight_strings = [str(flight) for flight in flights]
            flight_strings = [flight_string.replace(", ", "\n") for flight_string in flight_strings] #make new row for each variable
            print ("\n".join(flight_strings))
            print("----------------------------")

#endregion

#region CRUD users

def create_new_user(db: Session, user:schemas.UserCreate) -> int:
    new_user = dbm.User(email = user.email, hashed_password = user.hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user) # to get an id to the user
    return new_user.id

def delete_user(db: Session, email: str, password_hash: str):
    if not check_if_user_email_matches_user_password(db, email, password_hash): #the password not matches the email 
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"email: {email} not matching the given password")
    
    user_to_delete = db.query(dbm.User).filter(dbm.User.email == email).first() #find the user in the data base

    if not user_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(user_to_delete)

    db.commit()

def get_user_by_email(db: Session, email: str) -> dbm.User:
    """
    find the user with the given email if not founded it will raise http 404 error
    """
    user = db.query(dbm.User).filter(dbm.User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {email} not found."
        )
    return user

def get_user_by_id(db: Session, user_id: int) -> dbm.User:
    user = db.query(dbm.User).filter(dbm.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found."
        )
    return user

def get_user_id_by_flight_id(db: Session, flight_id:int) -> int:
    return get_flight_by_id(db, flight_id).user_id

def check_if_user_email_matches_user_password(db: Session, email:str, password_hash:str) -> bool:
    user = db.query(dbm.User).filter(dbm.User.email == email).first()
    return user.hashed_password == password_hash

#endregion

#region CRUD flights

def _dbm_flight_from_models_flight(flight: schemas.Flight) -> dbm.Flight:
    flight_data = flight.model_dump() #makes a dict from the flight values

    #remove the pydantic items and send there valriabels seprately
    more_criteria_data = flight_data.pop('more_criteria', {})
    best_found_data = flight_data.pop('best_found', {})

    db_flight = dbm.Flight(
        **flight_data,  
        more_criteria=more_criteria_data,
        best_found=best_found_data
    )

    return db_flight

def add_flight(db: Session, flight: schemas.Flight) -> int:
    """
    adding flight to a user and returning the flight id
    if the user id isnt a real user id it will return http 404
    if the user has a flight with the same values he cant trace another one it will return http 409
    """
    try:
        db_flight = _dbm_flight_from_models_flight(flight)

        db.add(db_flight)
        db.commit()
        db.refresh(db_flight)
        return db_flight.flight_id
    
    except IntegrityError as e:
        db.rollback()
        if "foreign key constraint" in str(e).lower() and "user_id" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {flight.user_id} not found."
            )
        elif "_user_flight_uc" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This flight route is already being tracked by this user."
            )
        raise

def get_all_user_flights(db: Session, user_email: str) -> list[dbm.Flight]:
    user_in_db = get_user_by_email(db, user_email)

    return user_in_db.flights_to_track

def get_flight_by_id(db: Session, flight_id:int) -> dbm.Flight:
    """
    if the flight isnt in the db it will raise an http 404 error
    """
    flight_in_db = db.query(dbm.Flight).filter(dbm.Flight.flight_id == flight_id).first()

    if not flight_in_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flight with ID {flight_id} not found."
        )
    return flight_in_db

def check_if_data_changed(last_flight: dbm.Flight, update_data: dict) -> bool:
    core_fields_to_check = [
        "departure_airport",
        "arrival_airport",
        "requested_date",
        "target_price",
        "more_criteria"
    ]

    for field_name in core_fields_to_check:
        if field_name in update_data:
            current_db_value = getattr(last_flight, field_name)
            if isinstance(current_db_value, dict): # for JSONB/JSON
                current_db_value = schemas.MoreCriteria(**current_db_value) if field_name == "more_criteria" else schemas.BestFlightFound(**current_db_value)
            
            new_value_from_client = update_data[field_name]
            if isinstance(new_value_from_client, schemas.BaseModel):
                if field_name == "more_criteria":
                    if current_db_value.model_dump() != new_value_from_client.model_dump():
                        return True
            elif str(current_db_value) != str(new_value_from_client):
                return True
            
    return False

def update_flight(db: Session, user_id:int, flight: schemas.Flight):
    get_user_by_id(db, user_id) #if the user not in the db it will raise an http 404 error
    db_flight = get_flight_by_id(db, flight.flight_id) #if the flight not in the db it will raise an http 404 error
    
    if db_flight.user_id != user_id:
        raise HTTPException (status_code=status.HTTP_403_FORBIDDEN, detail=f"user {user_id} not allowed to do changes in other users flights")

    update_data = flight.model_dump(exclude_unset=True)

    data_changed = check_if_data_changed(db_flight, update_data)

    for key, value in update_data.items():
        if key == "more_criteria":
            setattr(db_flight, key, value.model_dump() if value is not None else {})
        elif key == "best_found":
            if data_changed:
                setattr(db_flight, key, None)
            else:
                setattr(db_flight, key, value.model_dump() if value is not None else {})
        elif key in ["requested_date", "last_checked"]:
            if value is not None:
                if key == "last_checked" and data_changed:
                    setattr(db_flight, key, None) 
                else:
                    try:
                        format_string = "%Y-%m-%d" if key == "requested_date" else "%Y-%m-%d %H:%M:%S"
                        setattr(db_flight, key, datetime.strptime(value, format_string))
                    except ValueError:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid date format for {key}. Use {format_string}."
                        )
            else:
                setattr(db_flight, key, None) 
        else:
            setattr(db_flight, key, value)

    try:
        db.commit()
        db.refresh(db_flight)
        return db_flight
    
    except IntegrityError as e:
        db.rollback()
        if "_user_flight_route_uc" in str(e):
             raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An identical flight route is already being tracked by this user."
            )
        raise

def update_all_flights_details(db: Session, update_func):
    flights = db.query(dbm.Flight).all() #get all the flights
    
    for flight in flights:
        try:
            new_flight = update_func(flight)
            update_flight(db, new_flight.user_id, new_flight)
        except ValueError as e:
            raise HTTPException (status_code=status.HTTP_400_BAD_REQUEST, detail=f"the update func didnt return the flight good: {flight}")

def delete_flight_by_id(db: Session, flight_id: int):
    db_flight = get_flight_by_id(db, flight_id) #check if the flight exists

    try:
        db.delete(db_flight)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during flight deletion: {e}"
        )

#endregion

#region tests

def test_restart():
    db_connection._restart()
    #test_add_user()
    db = next(db_connection.get_db())
    _create_five_dummy_users(db)
    #update_flight(db = db, user_id=5, flight = schemas.Flight(flight_id=5,user_id=5, departure_airport="BKK", arrival_airport="TLV", requested_date="2025-12-12", target_price=600))
    _print_all_users_and_flights(db)
        
test_restart()
#endregion