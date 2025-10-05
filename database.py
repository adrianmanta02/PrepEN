from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker 
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os 

load_dotenv()

# define database location 
SQLALCHEMY_DATABASE_URL = os.getenv('DATABASE_URL')

# create the application engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# create the session local 
SessionLocal = sessionmaker(bind = engine, autoflush = False, autocommit = False)

# create the database object that is able to interact with the tables 
Base = declarative_base()
