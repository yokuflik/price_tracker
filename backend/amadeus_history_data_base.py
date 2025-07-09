from sqlalchemy.orm import Session
import pandas as pd
import schemas
import data_base_models as dbm

def _printAllData(db: Session):
    query = "SELECT * FROM flight_search_history;"
    df = pd.read_sql(query, db.bind)
    print(df)

def insert_search(db: Session, flight: schemas.Flight):
    db.add(flight)
    db.commit()