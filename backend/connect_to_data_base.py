from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from config import settings

#create the engin that connects to the sql data
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#creaate the tables in the data base if not exists
#Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_new_connection():
    return next(get_db())

def _restart():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def get_all_tables():
    try:
        inspector = inspect(engine)

        all_table_names = inspector.get_table_names()

        if all_table_names:
            print("all tables in the database:")
            for table_name in all_table_names:
                print(f"- {table_name}")
        else:
            print("לא נמצאו טבלאות במסד הנתונים שלך.")

    except Exception as e:
        print(f"אירעה שגיאה בעת ניסיון לקבל את שמות הטבלאות: {e}")
