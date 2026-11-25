"""Restaurant 360: academic REST API and browser interface."""
import os
import sqlite3
from contextlib import contextmanager, closing
from datetime import date
from pathlib import Path
from secrets import token_urlsafe
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
MENU = {'Hamburguesa': 25000, 'Pizza': 32000, 'Ensalada': 18000, 'Limonada': 8000}

class Reservation(BaseModel):
    customer: str = Field(min_length=2, max_length=80)
    day: date
    slot: str = Field(pattern=r'^(12:00|14:00|18:00|20:00)$')
    table_id: int = Field(ge=1, le=8)
    guests: int = Field(ge=1, le=4)

class Order(BaseModel):
    customer: str = Field(min_length=2, max_length=80)
    item: str
    quantity: int = Field(ge=1, le=20)

class Login(BaseModel):
    password: str

def create_app(db_path=None):
    app = FastAPI(title='Restaurante 360', version='1.0.0')
    path = db_path or os.getenv('DATABASE_PATH', str(ROOT / 'restaurant.db'))
    tokens = set()

    @contextmanager
    def db():
        with closing(sqlite3.connect(path, timeout=10)) as conn:
            conn.row_factory = sqlite3.Row
            with conn:
                yield conn

    with db() as conn:
        conn.executescript('''CREATE TABLE IF NOT EXISTS reservations(id INTEGER PRIMARY KEY, customer TEXT NOT NULL, day TEXT NOT NULL, slot TEXT NOT NULL, table_id INTEGER NOT NULL, guests INTEGER NOT NULL, UNIQUE(day, slot, table_id));
        CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, customer TEXT NOT NULL, item TEXT NOT NULL, quantity INTEGER NOT NULL, total INTEGER NOT NULL);''')

    def admin(authorization: str = Header(default='')):
        if not authorization.startswith('Bearer ') or authorization[7:] not in tokens:
            raise HTTPException(401, 'Acceso administrativo requerido')

    @app.get('/')
    def home():
        return FileResponse(ROOT / 'templates/index.html')

    @app.get('/health')
    def health():
        with db() as conn:
            conn.execute('SELECT 1')
        return {'status': 'ok'}

    @app.get('/api/menu')
    def menu():
        return MENU

    @app.get('/api/availability')
    def availability(day: date, slot: str):
        if slot not in ('12:00', '14:00', '18:00', '20:00'):
            raise HTTPException(422, 'Horario inválido')
        with db() as conn:
            busy = {r[0] for r in conn.execute('SELECT table_id FROM reservations WHERE day=? AND slot=?', (str(day), slot))}
        return {'available': [i for i in range(1, 9) if i not in busy]}

    @app.post('/api/reservations', status_code=201)
    def reserve(data: Reservation):
        if data.day < date.today():
            raise HTTPException(422, 'No se permiten fechas pasadas')
        try:
            with db() as conn:
                cursor = conn.execute('INSERT INTO reservations(customer,day,slot,table_id,guests) VALUES (?,?,?,?,?)', (data.customer, str(data.day), data.slot, data.table_id, data.guests))
                ident = cursor.lastrowid
        except sqlite3.IntegrityError as exc:
            raise HTTPException(409, 'Mesa ya reservada para ese horario') from exc
        return {'id': ident, 'confirmation': f'RES-{ident:05d}', 'status': 'confirmada'}

    @app.post('/api/orders', status_code=201)
    def order(data: Order):
        if data.item not in MENU:
            raise HTTPException(422, 'Producto no disponible')
        total = MENU[data.item] * data.quantity
        with db() as conn:
            ident = conn.execute('INSERT INTO orders(customer,item,quantity,total) VALUES (?,?,?,?)', (data.customer, data.item, data.quantity, total)).lastrowid
        return {'id': ident, 'total': total, 'confirmation': f'PED-{ident:05d}', 'status': 'recibido'}

    @app.post('/api/login')
    def login(data: Login):
        from secrets import compare_digest
        password = os.getenv('ADMIN_PASSWORD')
        if not password:
            raise HTTPException(503, 'Configure ADMIN_PASSWORD en el servidor')
        if not compare_digest(data.password.encode(), password.encode()):
            raise HTTPException(401, 'Credenciales incorrectas')
        token = token_urlsafe(32)
        tokens.add(token)
        return {'token': token}

    @app.get('/api/reports', dependencies=[Depends(admin)])
    def reports():
        with db() as conn:
            reservations = conn.execute('SELECT COUNT(*) FROM reservations').fetchone()[0]
            orders, revenue = conn.execute('SELECT COUNT(*), COALESCE(SUM(total),0) FROM orders').fetchone()
        return {'reservations': reservations, 'orders': orders, 'revenue': revenue}

    app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')
    return app

app = create_app()
