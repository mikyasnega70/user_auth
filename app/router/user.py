from fastapi import APIRouter, HTTPException, Request, Depends
from starlette import status
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from typing import Annotated
from ..database import Asyncsessionlocal
from ..models import Users
from .auth import get_current_user
from ..limiter import limiter
from datetime import datetime

router = APIRouter(
    prefix='/users',
    tags=['users']
)

class UserCreate(BaseModel):
    email:EmailStr=Field(alias='Email')
    password:str = Field(alias='Password')

    model_config = ConfigDict(populate_by_name=True)

class UserResponse(BaseModel):
    id:int
    email:EmailStr
    is_active:bool
    created_at:datetime

async def get_db():
    async with Asyncsessionlocal() as session:
        yield session

db_dependency = Annotated[AsyncSession, Depends(get_db)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.post('/register', status_code=status.HTTP_201_CREATED)
@limiter.limit('30/minute')
async def register_user(db:db_dependency, request:Request, newuser:UserCreate):
    db_user = await db.execute(select(Users).where(Users.email == newuser.email))
    db_user = db_user.scalar_one_or_none()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email already registered')
    
    user_model = Users(
        email=newuser.email,
        hashed_password=bcrypt_context.hash(newuser.password)
    )

    db.add(user_model)
    await db.commit()
    return {'msg':'user created'}

@router.get('/me', status_code=status.HTTP_200_OK, response_model=UserResponse)
@limiter.limit('30/minute')
async def get_user(db:db_dependency, request:Request, user:user_dependency):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    
    result = await db.scalars(select(Users).where(Users.email == user.get('email')))
    user_model = result.first()
    return user_model




