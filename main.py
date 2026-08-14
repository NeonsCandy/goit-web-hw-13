from fastapi import FastAPI, Depends, HTTPException, Query, status, Request, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import cloudinary
import cloudinary.uploader

from database import engine, get_db, Base
from config import settings
import models, schemas, crud, auth

cloudinary.config(
    cloud_name=settings.CLOUDINARY_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)

limiter = Limiter(key_func=get_remote_address)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Contacts API Secure")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.post("/auth/signup", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def signup(body: schemas.UserModel, db: Session = Depends(get_db)):
    exist_user = crud.get_user_by_email(db, email=body.email)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    new_user = crud.create_user(db, body)
    return new_user

@app.post("/auth/login", response_model=schemas.TokenModel)
def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=body.username)
    if user is None or not auth.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    access_token = auth.create_access_token(data={"sub": user.email})
    refresh_token = auth.create_refresh_token(data={"sub": user.email})
    crud.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.patch("/users/avatar", response_model=schemas.UserResponse)
def update_avatar(file: UploadFile = File(...), current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Оновлення аватара користувача"""
    r = cloudinary.uploader.upload(file.file, public_id=f'ContactsApp/{current_user.email}', overwrite=True)
    src_url = cloudinary.CloudinaryImage(f'ContactsApp/{current_user.email}').build_url(width=250, height=250, crop='fill', version=r.get('version'))
    
    current_user.avatar = src_url
    db.commit()
    return current_user

@app.post("/contacts/", response_model=schemas.ContactResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute") 
def create_contact(request: Request, contact: schemas.ContactCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.create_contact(db=db, contact=contact, user_id=current_user.id)

@app.get("/contacts/", response_model=list[schemas.ContactResponse])
def read_contacts(name: str = Query(None), surname: str = Query(None), email: str = Query(None), skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.get_contacts(db, user_id=current_user.id, name=name, surname=surname, email=email, skip=skip, limit=limit)

@app.get("/contacts/{contact_id}", response_model=schemas.ContactResponse)
def read_contact(contact_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    contact = crud.get_contact_by_id(db, contact_id=contact_id, user_id=current_user.id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact