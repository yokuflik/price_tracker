from pydantic import BaseModel, EmailStr, confloat, Field
from typing import Optional
from datetime import date, datetime

class UserInfo(BaseModel):
    email: EmailStr
    hash_password: str

class BestFlightFound(BaseModel):
    price: Optional[confloat(gt=0)] = None
    time: Optional[str] = None
    airline: Optional[str] = None

DEPARTMENTS = ["Tourists", "Business", "First"]
class MoreCriteria(BaseModel):
    connection: int = 0
    max_connection_hours: Optional[float] = None
    department: str = Field(default=DEPARTMENTS[0])

    is_round_trip: bool = True
    return_date: Optional[str] = None

    flexible_days_before: int = 0
    flexible_days_after: int = 0

    custom_name: Optional[str] = None

class Flight(BaseModel):
    flight_id: Optional[int] = None
    user_id: int
    departure_airport: str
    arrival_airport: str
    requested_date: str
    target_price: confloat(gt=0) #more then 0
    last_checked: Optional[str] = None
    last_price_found: Optional[float] = None
    notify_on_any_drop: bool = False
    more_criteria: MoreCriteria = Field(default_factory=MoreCriteria)
    best_found: BestFlightFound = Field(default_factory=BestFlightFound)
    