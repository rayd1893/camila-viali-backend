from dotenv import load_dotenv
from os import getenv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()

MYSQL_USER = getenv('MYSQL_USER')
MYSQL_PWD = getenv('MYSQL_PASSWORD')
MYSQL_HOST = getenv('MYSQL_HOST')
MYSQL_DB = getenv('MYSQL_DB')

engine = create_engine('mysql+mysqldb://{}:{}@{}/{}'.format(MYSQL_USER, MYSQL_PWD, MYSQL_HOST, MYSQL_DB))

SessionLocal = sessionmaker(expire_on_commit=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()