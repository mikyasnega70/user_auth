from utils import *
from fastapi import status
from app.router.user import get_db, get_current_user
from sqlalchemy import select
import pytest

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

# @pytest.mark.asyncio
def test_register_user(test_user, client):
    response = client.post('/users/register', json={'email':'newtest@gmail.com', 'password':'newtestpassword'})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {'msg':'user created'}

def test_get_user(test_user, client):
    response = client.get('/users/me')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        'id': test_user.id,
        'email': test_user.email,
        'is_active': test_user.is_active,
        'created_at': test_user.created_at.isoformat()
    }



