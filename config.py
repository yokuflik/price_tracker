#this is the flie with all the global variabels

USER_NOT_FOUND_ERROR = "No user found with IP"
CONNECTION_PROBLEM = "Problem with the connection"

USER_ADDED_SUCCESSFULLY = "The user was added"
USER_ADD_FAILED = "The user add failed"

USER_DELETED_SUCCESSFULLY = "The user was deleted"
USER_DELETE_FAILED = "The user delete failed"

FLIGHT_ADDED_SUCCESSFULLY = "The flight was added"
FLIGHT_ADD_FAILED = "The flight add failed"

FLIGHT_DELETED_SUCCESSFULLY = "The flight was deleted"
FLIGHT_DELETE_FAILED = "The flight delete failed"

FLIGHT_UPDATED_SUCCESSFULLY = "The flight updated successfully"
FLIGHT_UPDATE_FAILED = "Flight updated failed"

class Flight:
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