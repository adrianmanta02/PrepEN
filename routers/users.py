from fastapi import APIRouter, HTTPException, Depends, Request, status, Header
from fastapi.templating import Jinja2Templates
from typing import Optional
from models import Users
from .auth import db_dependency, get_current_user, verify_token
from .materials import redirect_to_login

router = APIRouter(prefix="/users", tags=["users"])
templates = Jinja2Templates(directory="templates")

# Helper function to get teacher from Authorization header
async def get_teacher_from_header(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Not authenticated")
    
    # extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid authorization header format")
    
    # verify token
    user = await verify_token(token)
    
    if user.get("role") != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only teachers can perform this action")
    
    return user

@router.get("/all-users")
async def render_all_users_page(request: Request, db: db_dependency):
    try:
        token = request.cookies.get("access_token")
        teacher = await verify_token(token)
        
        if not teacher or teacher.get("role") != "teacher":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        users = db.query(Users).all()
        return templates.TemplateResponse("users.html", {
            "request": request, 
            "users": users, 
            "user": teacher
        })
    except Exception as e:
        return redirect_to_login()

# PATCH: approve
@router.patch("/{user_id}/approve")
async def approve_user(user_id: int, db: db_dependency):

    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_approved = True
    db.commit()
    db.refresh(user)
    
    return {"detail": f"User {user.username} approved", "id": user.id}

# PATCH: revoke
@router.patch("/{user_id}/revoke")
async def revoke_user(user_id: int, 
                        db: db_dependency):
    
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_approved = False
    db.commit()
    db.refresh(user)
    
    return {"detail": f"User {user.username} approval revoked", "id": user.id}

# DELETE: dismiss
@router.delete("/{user_id}")
async def dismiss_user(user_id: int, 
                       db: db_dependency):
    
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(user)
    db.commit()
    
    return {"detail": f"User {user.username} dismissed", "id": user.id}
