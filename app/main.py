from fastapi import FastAPI, Request, Depends, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import database, models
from app.schemas import UserCreate

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    models.Base.metadata.create_all(bind=models.engine)

templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup(login: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = database.get_user_by_login(db, login)
    if user:
        raise HTTPException(status_code=400, detail="Login already registered")

    database.create_user(db=db, user=UserCreate(login=login, password=password))
    return RedirectResponse(url="/signin", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/signin", response_class=HTMLResponse)
async def signin_form(request: Request):
    return templates.TemplateResponse("signin.html", {"request": request})

@app.post("/signin")
async def signin(login: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = database.get_user_by_login(db, login)
    if not user or not database.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect login or password")

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="user", value=login)
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/signin")
    response.delete_cookie(key="user")
    return response
