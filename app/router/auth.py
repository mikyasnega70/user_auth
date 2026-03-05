from fastapi import APIRouter, HTTPException, Request, Depends
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from typing import Annotated
from jose import jwt, JWTError
from ..database import Asyncsessionlocal
from ..models import Users
from ..limiter import limiter
from dotenv import load_dotenv
from datetime import timedelta, timezone, datetime
import os

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

load_dotenv()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
EXPIRES = int(os.getenv('ACCESS_TOKEN_EXPIRES', 30))

async def get_db():
    async with Asyncsessionlocal() as session:
        yield session

db_dependency = Annotated[AsyncSession, Depends(get_db)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

class Token(BaseModel):
    access_token:str
    refresh_token:str
    token_type:str

class TokenData(BaseModel):
    email:EmailStr | None = None

class RefreshRequest(BaseModel):
    refresh_token:str

def create_access_token(data:dict, expires:timedelta=None):
    to_encode = data.copy()

    if expires:
        expire = datetime.now(timezone.utc) + expires
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRES)

    to_encode.update({'exp':expire, 'type':'access'})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data:dict, expires:timedelta=None):
    to_encode = data.copy()
    if expires:
        expire = datetime.now(timezone.utc) + expires
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    
    to_encode.update({'exp':expire, 'type':'refresh'})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(db:db_dependency, token:Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get('type') != 'access':
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
        user_email:EmailStr = payload.get('sub')
        if not user_email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
        token_data = TokenData(email=user_email)
        result = await db.execute(select(Users).where(Users.email == token_data.email))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
        
        return {'email':user.email}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')

@router.post('/token', response_model=Token)
@limiter.limit('30/minute')
async def login_access(db:db_dependency, request:Request, form:Annotated[OAuth2PasswordRequestForm, Depends()]):
    query = await db.execute(
        select(Users).where(Users.email == form.username)
    )

    user = query.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')

    if not bcrypt_context.verify(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')

    access_token = create_access_token({'sub':user.email})
    refresh_token = create_refresh_token({'sub':user.email})
    return {'access_token':access_token, 'refresh_token':refresh_token, 'token_type':'bearer'}

@router.post('/refresh')
@limiter.limit('10/minute')
async def refresh_token(db:db_dependency, request:Request, data:RefreshRequest):
    try:
        payload = jwt.decode(data.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get('type') != 'refresh':
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
        
        user_email:EmailStr = payload.get('sub')
        if not user_email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
        
        result = await db.execute(select(Users).where(Users.email == user_email))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
        
        access_token = create_access_token({'sub':user.email})
        return {'new_access_token':access_token}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')





