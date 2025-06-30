from pydantic import BaseModel, EmailStr, confloat
from typing import Optional

class UserInfo(BaseModel):
    email: EmailStr
    hash_password: str

class BestFlightFound(BaseModel):
    price: confloat (gt=0) #more then zero
    time: str
    airline: str

class Flight(BaseModel):
    flight_id: Optional[int] = None  # ייווצר אוטומטית
    user_id: float
    departure_airport: str
    arrival_airport: str
    requested_date: str  # תוכל להפוך ל־datetime אם תרצה
    target_price: confloat (gt=0) #more then 0
    last_checked: Optional[str] = None
    last_price_found: Optional[float] = None
    notify_on_any_drop: bool = False
    best_found: Optional[BestFlightFound] = None
    

    @classmethod
    def from_tuple(cls, tup):
        return cls(
            flight_id=tup[0],
            user_id=tup[1],
            departure_airport=tup[2],
            arrival_airport=tup[3],
            requested_date=tup[4],
            target_price=tup[5],
            last_checked=tup[6],
            last_price_found = tup[7],
            notify_on_any_drop=bool(tup[8]),
            best_found=BestFlightFound(
                price=float(tup[9]),
                time=tup[10],
                airline=tup[11]
            ) if tup[9] and tup[10] and tup[11] else None
        )
