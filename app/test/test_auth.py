from utils import *
from fastapi import status
from app.router.auth import get_db, create_access_token, create_refresh_token, get_current_user, SECRET_KEY, ALGORITHM
from jose import jwt

app.dependency_overrides[get_db] = override_get_db

def test_create_access_token():
    data = {'sub':'test@gmail.com'}
    token = create_access_token(data)

    decode_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decode_token['sub'] == data.get('sub')

# @pytest.mark.asyncio
def test_login_access(test_user, client):
    response = client.post('/auth/token', data={'username':'test@gmail.com', 'password':'testpassword'})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert 'access_token' in data

# @pytest.mark.asyncio
def test_refresh_token(test_user, client):
    data = {'sub':'test@gmail.com'}
    refresh_token = create_refresh_token(data)
    response = client.post('/auth/refresh', json={'refresh_token':refresh_token})
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    decode = jwt.decode(data['new_access_token'], SECRET_KEY, algorithms=[ALGORITHM])
    assert decode['sub'] == 'test@gmail.com'

