from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from app import create_app

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('ADMIN_PASSWORD', 'test-only-password')
    with TestClient(create_app(tmp_path / 'test.db')) as c:
        yield c

@pytest.fixture
def reservation():
    return dict(customer='Ana', day=str(date.today()+timedelta(days=1)), slot='18:00', table_id=1, guests=2)

def test_home(client):
    assert 'Restaurante 360' in client.get('/').text

def test_health(client):
    assert client.get('/health').json() == {'status':'ok'}

def test_menu(client):
    assert client.get('/api/menu').json()['Pizza'] == 32000

def test_reservation(client,reservation):
    r=client.post('/api/reservations',json=reservation)
    assert r.status_code == 201 and r.json()['confirmation'].startswith('RES-')

def test_duplicate(client,reservation):
    assert client.post('/api/reservations',json=reservation).status_code == 201
    assert client.post('/api/reservations',json=reservation).status_code == 409

def test_availability(client,reservation):
    client.post('/api/reservations',json=reservation)
    r=client.get('/api/availability',params={'day':reservation['day'],'slot':'18:00'})
    assert r.json()['available'] == list(range(2,9))

def test_invalid_slot(client,reservation):
    assert client.get('/api/availability',params={'day':reservation['day'],'slot':'09:00'}).status_code == 422

def test_past(client,reservation):
    reservation['day']='2000-01-01'
    assert client.post('/api/reservations',json=reservation).status_code == 422

def test_capacity(client,reservation):
    reservation['guests']=5
    assert client.post('/api/reservations',json=reservation).status_code == 422

def test_order(client):
    r=client.post('/api/orders',json={'customer':'Ana','item':'Pizza','quantity':2})
    assert r.status_code == 201 and r.json()['total'] == 64000

def test_unknown_product(client):
    assert client.post('/api/orders',json={'customer':'Ana','item':'Otro','quantity':1}).status_code == 422

def test_quantity(client):
    assert client.post('/api/orders',json={'customer':'Ana','item':'Pizza','quantity':0}).status_code == 422

def test_protected(client):
    assert client.get('/api/reports').status_code == 401

def test_wrong_password(client):
    assert client.post('/api/login',json={'password':'wrong'}).status_code == 401

def test_reports(client,reservation):
    client.post('/api/reservations',json=reservation)
    client.post('/api/orders',json={'customer':'Ana','item':'Pizza','quantity':2})
    token=client.post('/api/login',json={'password':'test-only-password'}).json()['token']
    assert client.get('/api/reports',headers={'Authorization':'Bearer '+token}).json() == {'reservations':1,'orders':1,'revenue':64000}

def test_missing_admin(client,monkeypatch):
    monkeypatch.delenv('ADMIN_PASSWORD')
    assert client.post('/api/login',json={'password':'any'}).status_code == 503
