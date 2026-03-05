from fastapi import FastAPI
from fastapi.testclient import TestClient
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete
from app.main import app
from app.models import Users, Base
from app.router.auth import bcrypt_context
import pytest

DATABASE_URL = 'sqlite+aiosqlite:///./test.db'
engine = create_async_engine(DATABASE_URL)

TestAsyncsessionlocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)

@asynccontextmanager
async def lifespan_setup(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()



@pytest.fixture
def client():
    app.router.lifespan_context = lifespan_setup
    with TestClient(app) as c:
        yield c

async def override_get_db():
    async with TestAsyncsessionlocal() as session:
        yield session

async def override_get_current_user():
    return {'email':'test@gmail.com'}

@pytest.fixture
async def test_user():
    async with TestAsyncsessionlocal() as db:
        user = Users(
            email='test@gmail.com',
            hashed_password=bcrypt_context.hash('testpassword')
        )
        db.add(user)
        await db.commit()
        yield user

        async with engine.begin() as conn:
            await conn.execute(delete(Users))

