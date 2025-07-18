from sqlalchemy import Column, Integer,Float, String, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship

from connect_to_data_base import Base

from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True) 
    email = Column(String, unique=True, index=True, nullable=False) 
    hashed_password = Column(String, nullable=False) 

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', hash_password={self.hashed_password})>"
    
    flights_to_track = relationship("Flight", back_populates="owner")

class baseFlight(Base):
    __abstract__ = True
    departure_airport = Column(String, nullable=False)
    arrival_airport = Column(String, nullable=False)
    requested_date = Column(DateTime, nullable=False)
    target_price = Column(Float, nullable=False)

    more_criteria = Column(JSON, nullable=False, default={})

class Flight(baseFlight):
    __tablename__ = "flights"

    flight_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="flights_to_track")

    last_checked = Column(DateTime, nullable=True)
    last_price_found = Column(Float, nullable=True)
    notify_on_any_drop = Column(Boolean, default=False, nullable=False)

    best_found = Column(JSON, nullable=False, default={}) 

    def __repr__(self):
        return (f"<Flight(flight_id={self.flight_id}, "
                f"user_id={self.user_id}, "
                f"departure='{self.departure_airport}', "
                f"arrival='{self.arrival_airport}', "
                f"requested_date={self.requested_date.strftime('%Y-%m-%d') if self.requested_date else 'N/A'}, "
                f"target_price={self.target_price}, "
                f"last_price_found={self.last_price_found})"
                f"more criteria={self.more_criteria}"
                f"best found={self.best_found}>")

class AmadeusFlight(baseFlight):
    __tablename__ = "amadeus_flights"

    id = Column(Integer, primary_key=True, index=True)
    time_stamp = Column(DateTime, nullable=False, default=datetime.now)

class AddFlight(baseFlight):
    __tablename__ = "flight_search_history"

    id = Column(Integer, primary_key=True, index=True)
    time_stamp = Column(DateTime, nullable=False, default=datetime.now)

class UpdateFlight(baseFlight):
    __tablename__ = "update_flight_history"

    id = Column(Integer, primary_key=True, index=True)
    time_stamp = Column(DateTime, nullable=False, default=datetime.now)

class UserGotFlight(baseFlight):
    __tablename__ = "user_got_flight_history"

    id = Column(Integer, primary_key=True, index=True)
    time_stamp = Column(DateTime, nullable=False, default=datetime.now)

class UserFlightExpired(baseFlight):
    __tablename__ = "user_flight_expired_history"

    id = Column(Integer, primary_key=True, index=True)
    time_stamp = Column(DateTime, nullable=False, default=datetime.now)

    best_found = Column(JSON, nullable=False, default={}) 