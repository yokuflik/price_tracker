from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from fastapi import HTTPException, status

from config import settings
import data_base_models as dbm
import connect_to_data_base as db_connection

import models

#region debug

def get_all_users(db:Session) -> list[dbm.User]:
    return db.query(dbm.User).all()

def create_five_dummy_users(db: Session):
    print("Creating 5 dummy users...")
    for i in range(1, 6):
        email = f"dummy_user_{i}@example.com"
        password = f"dummyPassword{i}!"
        user_data = models.UserCreate(email=email, hashed_password=password)

        if not get_user_by_email(db, email):
            create_new_user(db, user_data)
        else:
            print(f"  User {email} already exists. Skipping.")

#endregion

#region CRUD users

def create_new_user(db: Session, user:models.UserCreate) -> dbm.User:
    new_user = dbm.User(email = user.email, hashed_password = user.hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user) # to get an id to the user
    return new_user

def delete_user(db: Session, email: str, password_hash: str):
    if not check_if_user_email_matches_user_password(db, email, password_hash): #the password not matches the email 
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"email: {email} not matching the given password")
    
    user_to_delete = db.query(dbm.User).filter(dbm.User.email == email).first() #find the user in the data base

    if not user_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(user_to_delete)

    db.commit()

def get_user_by_email(db: Session, email: str) -> dbm.User:
    user = db.query(dbm.User).filter(dbm.User.email == email).first()
    return user

def get_user_by_id(db: Session, user_id: int) -> dbm.User:
    user = db.query(dbm.User).filter(dbm.User.id == user_id).first()
    return user

def check_if_user_email_matches_user_password(db: Session, email:str, password_hash:str) -> bool:
    user = db.query(dbm.User).filter(dbm.User.email == email).first()
    return user.hashed_password == password_hash

#endregion

#region tests

def test_add_user():
    db_session = next(db_connection.get_db())
    try:
        # 1. ניסיון ליצור משתמש חדש
        print("\n--- Creating a new user ---")
        user_email = "test2@example.com"
        user_password_hash = "some_secure_hash_here_123" # ב-prod: השתמש בגיבוב אמיתי
        new_user = create_new_user(db_session, user_email, user_password_hash)

        # 2. ניסיון ליצור משתמש שכבר קיים (צריך להיכשל אם ה-email unique)
        print("\n--- Attempting to create duplicate user ---")
        try:
            create_new_user(db_session, user_email, "another_hash")
        except Exception as e:
            print(f"Caught expected error (duplicate email): {e}")
            db_session.rollback() # חשוב לבצע rollback אחרי כשלון

        # 3. שליפת המשתמש שיצרנו לפי אימייל
        print("\n--- Retrieving user by email ---")
        fetched_user_by_email = get_user_by_email(db_session, user_email)
        if fetched_user_by_email:
            print(f"Retrieved user (email): {fetched_user_by_email.id}, {fetched_user_by_email.email}")
        else:
            print("User not found by email.")

        # 4. שליפת המשתמש שיצרנו לפי ID (אם נוצר)
        if new_user:
            print("\n--- Retrieving user by ID ---")
            fetched_user_by_id = get_user_by_id(db_session, new_user.id)
            if fetched_user_by_id:
                print(f"Retrieved user (ID): {fetched_user_by_id.id}, {fetched_user_by_id.email}")
            else:
                print("User not found by ID.")

    finally:
        # סגור את הסשן בסיום
        db_session.close()
        print("\nDatabase session closed.")

def test_restart():
    db_connection._restart()
    #test_add_user()
    db = next(db_connection.get_db())
    create_five_dummy_users(db)
    users = get_all_users(db)
    for user in users:
        print (user)

test_restart()

#endregion