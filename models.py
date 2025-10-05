from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey, DateTime, func, Boolean
from database import Base
from sqlalchemy.dialects.postgresql import ARRAY

class Users(Base): 
    __tablename__ = "users"

    id = Column(Integer, index = True, primary_key = True)
    firstname = Column(String)
    lastname = Column(String)
    username = Column(String, unique = True)
    email = Column(String, unique = True)
    password = Column(String)
    grade = Column(Integer)
    role = Column(String)
    is_approved = Column(Boolean)

class Materials(Base): 
    __tablename__ = "materials"

    id = Column(Integer, index = True, primary_key = True)
    title = Column(String)
    description = Column(String(6000))
    thumbnail = Column(String)
    files = Column(ARRAY(String)) 
    grade = Column(Integer)
    owner_id = Column(Integer, ForeignKey('users.id'))

    created_at = Column(DateTime(timezone = True), server_default = func.now())
    updated_at = Column(DateTime(timezone = True), onupdate = func.now())

    path = Column(String, nullable = True) # shows which subject the material belongs to 
