"""class Flight:
    def __init__(self, ip: str, departure_airport: str, arrival_airport: str, requested_date: str,
                 target_price: float, last_checked=None, last_checked_price=None,
                 best_price=None, best_time=None, best_airline=None):
        self.ip = ip
        self.departure_airport = departure_airport
        self.arrival_airport = arrival_airport
        self.requested_date = requested_date
        self.target_price = target_price
        self.last_checked = last_checked
        self.last_checked_price = last_checked_price
        self.best_price = best_price
        self.best_time = best_time
        self.best_airline = best_airline

    @classmethod
    def fromTupel(cls, tpl: tuple):
        if len(tpl) != 11:
            raise Exception('Problem with the tuple length')
        return Flight(tpl[1], tpl[2], tpl[3], tpl[4], tpl[5], tpl[6], tpl[7], tpl[8], tpl[9], tpl[10])
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            ip=data.get("ip"),
            departure_airport=data.get("departure_airport"),
            arrival_airport=data.get("arrival_airport"),
            requested_date=data.get("requested_date"),
            target_price=float(data.get("target_price")),
            last_checked=data.get("last_checked"),
            last_checked_price=data.get("last_checked_price"),
            best_price=data.get("best_price"),
            best_time=data.get("best_time"),
            best_airline=data.get("best_airline"),
        )

class UserInfo:
    def __init__(self, ip_address):
        self.ip_address = ip_address

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            ip_address=data.get("ip_address")
        )
        """

from pydantic import BaseModel, EmailStr
from typing import Optional

class UserInfo(BaseModel):
    email: EmailStr

class BestFlightFound(BaseModel):
    price: float
    time: str
    airline: str

class Flight(BaseModel):
    flight_id: Optional[int] = None  # ייווצר אוטומטית
    user_id: float
    departure_airport: str
    arrival_airport: str
    requested_date: str  # תוכל להפוך ל־datetime אם תרצה
    target_price: float
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
