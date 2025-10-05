from fastapi import APIRouter, Depends, HTTPException, status, Path, Request
from database import SessionLocal 
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from models import Users
import bcrypt  
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import Column, String, Integer 
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse 

router = APIRouter(
    prefix = "/auth",
    tags = ["auth"]
)

def get_db(): 
    db = SessionLocal() 
    try: 
        yield db 
    finally: 
        db.close() 

db_dependency = Annotated[Session, Depends(get_db)]

templates = Jinja2Templates(directory = "templates")

# ------------------------ PAGES --------------------------------
@router.get("/login-page")
async def render_login_page(request: Request): 
    return templates.TemplateResponse("login.html", {'request': request})

@router.get("/register-page")
async def render_register_page(request: Request):
    currentToken = request.cookies.get('access_token')
    if currentToken is None: 
        return templates.TemplateResponse("register.html", {'request': request})
    
    redirect_response = RedirectResponse(url = "/", status_code = status.HTTP_302_FOUND)
    return redirect_response

# ------------------------ ENDPOINTS ------------------------------

def authenticate_user(username: str, password: str, db: db_dependency):
    """
        Checks user's credentials according to the data stored in the database 
    """
    user = db.query(Users).filter(Users.username == username).first() 
    if not user: 
        return False
    
    # verify with bcrypt 
    password_bytes = password.encode('utf-8')[:72]  # truncate to 72 bytes
    hash_bytes = user.password.encode('utf-8')
    
    if not bcrypt.checkpw(password_bytes, hash_bytes): 
        return False
    
    return user

SECRET_KEY = "519944ac4c93fa81cc0992b8d8046dba6a3e31cb0b7f01a2b24d2fc09b21dd42"
ALGORITHM = "HS256"

def create_access_token(username: str, user_id: int, role: str, grade: int, is_approved: bool, expires_delta: timedelta): 
    """Creates a token for the logged-in user. The token will be used at the time of accessing a protected endpoint."""

    encode = {
        'sub': username,
        'id': user_id, 
        'role': role, 
        'grade': grade, 
        'is_approved': is_approved
    }   

    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm = ALGORITHM)

oauth2_bearer = OAuth2PasswordBearer(tokenUrl = "auth/token")

async def get_current_user(token: str = Depends(oauth2_bearer)): 
    """Receives and decodes the JWT token via OAuth2PasswordBearer object. 
    If an endpoint is protected, the function is going to verify if the token was falsificated,
    comparing the user's credentials with the payload(2nd part of the JWT). If suspicious, access will be denied."""

    try: 
        payload = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])
        sub = payload.get('sub')
        id = payload.get('id')
        role = payload.get('role')
        grade = payload.get('grade')
        is_approved = payload.get('is_approved')
        
        if sub is None or id is None: 
            raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Could not validate user.")
        
        if not is_approved: 
            raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail = "User not approved by teacher yet.")
        
        return {'sub': sub, 'id': id, 'role': role, 'grade': grade, 'is_approved': is_approved}
    
    except JWTError: 
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Could not validate user.")

@router.post("/token")
async def login_for_access_token(db: db_dependency, 
                                 form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):

    user = authenticate_user(username = form_data.username,
                             password = form_data.password, 
                             db = db)
    
    if not user: 
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Could not validate user.")

    if not user.is_approved: 
            raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail = "User not approved by teacher yet.")
        
    token = create_access_token(username = user.username, 
                                user_id = user.id, 
                                role = user.role,
                                grade = user.grade,
                                expires_delta = timedelta(minutes = 120),
                                is_approved = user.is_approved)

    return {'access_token': token, 'token_type': 'bearer'}

class CreateUserRequest(BaseModel): 
    firstname: str
    lastname: str
    username: str
    email: str
    password: str
    grade: int
    role: Optional[str] = "student"
    is_approved: bool = False

@router.post("/", status_code = status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest): 
    # Hash cu bcrypt
    password_bytes = create_user_request.password.encode('utf-8')[:72]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    
    new_user = Users(
        firstname = create_user_request.firstname,
        lastname = create_user_request.lastname,
        username = create_user_request.username,
        email = create_user_request.email,
        password = hashed.decode('utf-8'), 
        grade = create_user_request.grade,
        role = create_user_request.role,
        is_approved = create_user_request.is_approved
    )

    db.add(new_user)
    db.commit() 
    db.refresh(new_user)

@router.delete("/users/{userId}", status_code = status.HTTP_200_OK)
async def delete_user(db: db_dependency, userId: int = Path(gt = 0)): 
    user = db.query(Users).filter(Users.id == userId).first() 
    if user is None: 
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Could not find user with the ID given.")
    
    db.delete(user)
    db.commit() 

@router.get("/check-username", status_code = status.HTTP_200_OK)
async def check_username(db: db_dependency, username: str):
    searched_user = db.query(Users).filter(Users.username == username).first()
    return {'available': searched_user is None}

@router.get("/check-email", status_code = status.HTTP_200_OK)
async def check_email(db: db_dependency, email: str): 
    searched_user = db.query(Users).filter(Users.email == email).first() 
    return {'available': searched_user is None}

async def verify_token(token: str):
    """Verifies the token manually (e.g. directly from the cookie, not the header)""" 
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try: 
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get('sub')
        id = payload.get('id')
        role = payload.get('role')
        grade = payload.get('grade')
        is_approved = payload.get('is_approved')
        
        if sub is None or id is None: 
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")
        
        if not is_approved: 
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not approved by teacher yet.")
        
        return {'sub': sub, 'id': id, 'role': role, 'grade': grade, 'is_approved': is_approved}
    
    except JWTError as e:
        print(f"JWT Error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")