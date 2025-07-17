from datetime import date
from sqlite3 import IntegrityError
import holidays

from requests import Session
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship

import connect_to_data_base
from connect_to_data_base import Base, engine

#print (f"US Holidays: {us_holidays}")
# the below is the same, but takes a string:
us_holidays = holidays.country_holidays(country='US', years=2025)  # this is a dict-like object
israel_holidays = holidays.country_holidays(country='IL', years=2025)  # this is a dict-like object
thailand_holidays = holidays.country_holidays(country='TH', years=2025)  # this is a dict-like object

from sqlalchemy import Column, Integer, String, Date, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    iso_code = Column(String(2), unique=True, nullable=False)

    holidays = relationship("Holiday", back_populates="country")
    source_tourism_relations = relationship(
        "TourismRelation",
        foreign_keys="[TourismRelation.source_country_id]",
        back_populates="source_country"
    )

class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    year = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    type = Column(String, nullable=True) # e.g., "National", "Religious", "Cultural"

    country = relationship("Country", back_populates="holidays")

    __table_args__ = (
        UniqueConstraint('country_id', 'year', 'name', 'date', name='_country_year_holiday_uc'),
    )

class TourismRelation(Base):
    __tablename__ = "tourism_relations"

    id = Column(Integer, primary_key=True, index=True)
    source_country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    destination_country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    tourism_percentage = Column(DECIMAL(5,2), nullable=False)

    source_country = relationship(
        "Country",
        foreign_keys=[source_country_id],
        back_populates="source_tourism_relations"
    )
    destination_country = relationship(
        "Country",
        foreign_keys=[destination_country_id],
        back_populates="destination_tourism_relations"
    )

    __table_args__ = (
        UniqueConstraint('source_country_id', 'destination_country_id', name='_source_dest_year_uc'),
    )

def add_israeli_holidays_to_db(db:Session, years: list[int]):
    """
    Fetches Israeli holidays for specified years using the 'holidays' library
    and adds them to the database.
    """
    try:
        # 1. Ensure 'Israel' country exists in the database
        israel_country = db.query(Country).filter(Country.iso_code == "IL").first()
        if not israel_country:
            israel_country = Country(name="Israel", iso_code="IL")
            db.add(israel_country)
            db.commit()
            db.refresh(israel_country)
            print(f"Added new country to DB: {israel_country.name}")
        else:
            print(f"Country '{israel_country.name}' already exists in DB.")

        # 2. Fetch Israeli holidays
        # 'IL' is the ISO 3166-1 alpha-2 code for Israel
        # 'years' parameter specifies the years for which to fetch holidays
        israel_holidays = holidays.country_holidays('IL', years=years)

        # 3. Insert holidays into the database
        print(f"Adding holidays for Israel for years {years}...")
        for holiday_date_str, holiday_name in israel_holidays.items():
            try:
                # The 'holidays' library returns dates as strings for older Python versions,
                # or date objects. Convert to date object explicitly if needed.
                holiday_date = holiday_date_str if isinstance(holiday_date_str, date) else date.fromisoformat(str(holiday_date_str))

                holiday_year = holiday_date.year

                new_holiday = Holiday(
                    country_id=israel_country.id,
                    year=holiday_year,
                    name=holiday_name,
                    date=holiday_date,
                    type="National/Religious" # You might want to refine this based on actual holiday type if available
                )
                db.add(new_holiday)
                db.commit() # Commit each holiday to handle potential duplicates more gracefully
                print(f"  Added: {holiday_name} on {holiday_date} ({holiday_year})")
            except IntegrityError:
                db.rollback() # Rollback on duplicate entry
                print(f"  Skipping (already exists): {holiday_name} on {holiday_date} ({holiday_year})")
            except Exception as e:
                db.rollback()
                print(f"  Error adding {holiday_name} on {holiday_date}: {e}")

        print("Finished adding holidays.")

    except Exception as e:
        db.rollback()
        print(f"An error occurred during the process: {e}")
    finally:
        db.close()

# --- Example Usage ---

if __name__ == "__main__":

    # Add holidays for Israel for 2024 and 2025
    Base.metadata.create_all(bind=engine)

    db = connect_to_data_base.get_new_connection()
    add_israeli_holidays_to_db(db, years=[2024, 2025])

    # You can verify by querying the database afterwards
    # from data_base_models import Holiday, Country
    """israel = db.query(Country).filter(Country.iso_code == "IL").first()
    if israel:
        holidays_2024 = db.query(Holiday).filter(Holiday.country_id == israel.id, Holiday.year == 2024).all()
        print("\nIsraeli Holidays in 2024:")
        for h in holidays_2024:
            print(f"- {h.name} on {h.date}")"""