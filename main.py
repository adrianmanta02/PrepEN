from fastapi import FastAPI, Request
from models import * 
from database import Base, engine
from routers import auth, materials, users
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles 
from fastapi.templating import Jinja2Templates 
from routers.auth import get_current_user
from routers.materials import redirect_to_login

# instantiate main application 
app = FastAPI(prefix = "/home")
app.mount("/static", StaticFiles(directory = "static"), name = "static")

# start the session 
Base.metadata.create_all(bind = engine)

templates = Jinja2Templates(directory = "templates")

@app.get("/")
async def render_home_page(request: Request):
    currentToken = request.cookies.get('access_token')

    print(f"This is the token {currentToken}")
    user = None
    if currentToken is not None: 
        try: 
            user = await get_current_user(request.cookies.get('access_token'))
        except: 
            user = None

    return templates.TemplateResponse("index.html", {'request': request, 'user': user })

# include all routes 
app.include_router(auth.router)
app.include_router(materials.router)
app.include_router(users.router)