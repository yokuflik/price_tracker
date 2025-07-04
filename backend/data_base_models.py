from sqlalchemy import Column, Integer,Float, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from connect_to_data_base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True) # מפתח ראשי, אינדקס
    email = Column(String, unique=True, index=True, nullable=False) # אימייל (חובה, יחיד)
    hashed_password = Column(String, nullable=False) # סיסמה מגובבת (חובה)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', hash_password={self.hashed_password})>"
    
    flights_to_track = relationship("Flight", back_populates="owner")

class Flight(Base):
    __tablename__ = "flights"

    # מפתח ראשי
    id = Column(Integer, primary_key=True, index=True)

    # מפתח זר למשתמש שיצר את הטיסה למעקב
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    owner = relationship("User", back_populates="flights_to_track")

    # שדות טיסה בסיסיים
    departure_airport = Column(String, nullable=False)
    arrival_airport = Column(String, nullable=False)
    requested_date = Column(DateTime, nullable=False) # עדיף לשמור תאריכים כ-DateTime
    target_price = Column(Float, nullable=False)

    # שדות למעקב ומחיר אחרון
    last_checked = Column(DateTime, nullable=True) # זמן הבדיקה האחרונה
    last_price_found = Column(Float, nullable=True) # המחיר האחרון שנמצא
    notify_on_any_drop = Column(Boolean, default=False, nullable=False)

    # שדות מקוננים (MoreCriteria, BestFlightFound) - נשמור כ-JSONB
    # נשמור אותם כ-JSONB מכיוון שהם אובייקטים מקוננים.
    # זה מאפשר גמישות רבה יותר במבנה שלהם בעתיד.
    more_criteria = Column(JSON, nullable=False, default={}) # יכיל את הנתונים מ-MoreCriteria
    best_found = Column(JSON, nullable=False, default={}) # יכיל את הנתונים מ-BestFlightFound

    # יחסים למודלים אחרים (אם יש)
    # לדוגמה, קשר היסטוריית מעקב
    user_flight_history = relationship("UserFlightHistory", back_populates="flight")

    def __repr__(self):
        return (f"<Flight(id={self.id}, user_id={self.user_id}, "
                f"departure='{self.departure_airport}', arrival='{self.arrival_airport}', "
                f"target_price={self.target_price}, last_price={self.last_price_found})>")

