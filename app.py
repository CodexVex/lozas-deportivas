import os
from datetime import datetime, date, time, timedelta
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo
from flask import Flask, request, jsonify, render_template
from sqlalchemy import create_engine, select, ForeignKey, String, Numeric, DateTime, Time, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy.exc import IntegrityError

class Base(DeclarativeBase): pass
class Venue(Base):
    __tablename__ = 'venues'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(200))
class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True)
class Court(Base):
    __tablename__ = 'courts'
    id: Mapped[int] = mapped_column(primary_key=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey('venues.id'))
    name: Mapped[str] = mapped_column(String(100))
    sport: Mapped[str] = mapped_column(String(40))
    capacity: Mapped[int] = mapped_column(Integer)
    hourly_price: Mapped[Decimal] = mapped_column(Numeric(10,2))
class Schedule(Base):
    __tablename__ = 'schedules'
    id: Mapped[int] = mapped_column(primary_key=True)
    court_id: Mapped[int] = mapped_column(ForeignKey('courts.id'))
    weekday: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
class Rental(Base):
    __tablename__ = 'rentals'
    id: Mapped[int] = mapped_column(primary_key=True)
    court_id: Mapped[int] = mapped_column(ForeignKey('courts.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    event: Mapped[str] = mapped_column(String(120))
    sport: Mapped[str] = mapped_column(String(40))
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20),default='pending')
    payment_status: Mapped[str] = mapped_column(String(20),default='pending')
    total: Mapped[Decimal] = mapped_column(Numeric(10,2))

def serialize(obj):
    return {c.name: (v.isoformat() if isinstance(v,(date,time)) else float(v) if isinstance(v,Decimal) else v)
            for c in obj.__table__.columns for v in [getattr(obj,c.name)]}
def text_value(data,key,limit):
    v=data.get(key)
    if not isinstance(v,str) or not v.strip() or len(v.strip())>limit: raise ValueError(f'{key}: texto requerido, máximo {limit} caracteres')
    return v.strip()
def integer(data,key,minimum=1,maximum=1000000):
    v=data.get(key)
    if isinstance(v,bool) or str(v).strip() != str(int(v)) or not minimum<=int(v)<=maximum: raise ValueError(f'{key}: entero entre {minimum} y {maximum}')
    return int(v)
def interval(data):
    start=datetime.combine(date.fromisoformat(data['date']),time.fromisoformat(data['time']))
    duration=integer(data,'duration',30,720)
    if start.tzinfo is not None: raise ValueError('Usa hora local de Lima sin zona horaria')
    end=start+timedelta(minutes=duration)
    if start.date()!=end.date(): raise ValueError('La reserva debe terminar el mismo día')
    if start < datetime.now(ZoneInfo('America/Lima')).replace(tzinfo=None): raise ValueError('Elige una fecha y hora futuras')
    return start,end

def available(s,court_id,start,end):
    windows=s.scalars(select(Schedule).where(Schedule.court_id==court_id,Schedule.weekday==start.weekday())).all()
    in_window=any(w.start_time<=start.time() and w.end_time>=end.time() for w in windows)
    conflict=s.scalar(select(Rental.id).where(Rental.court_id==court_id,Rental.status!='cancelled',Rental.starts_at<end,Rental.ends_at>start).limit(1))
    return in_window and conflict is None

def create_app(url=None):
    app=Flask(__name__)
    engine=create_engine(url or os.environ.get('DATABASE_URL','postgresql+psycopg://lozas:lozas@localhost:5432/lozas'))
    app.config['ENGINE']=engine
    @app.errorhandler(ValueError)
    @app.errorhandler(KeyError)
    @app.errorhandler(TypeError)
    @app.errorhandler(InvalidOperation)
    def invalid(e): return jsonify(error=str(e)),400
    @app.errorhandler(IntegrityError)
    def integrity(e): return jsonify(error='Registro duplicado o referencia inválida'),409
    @app.get('/')
    def home(): return render_template('index.html')
    @app.get('/health')
    def health():
        with Session(engine) as s: s.execute(select(Court.id).limit(1))
        return jsonify(status='ok')
    @app.get('/users')
    @app.get('/venues')
    def catalog():
        model=User if request.path=='/users' else Venue
        with Session(engine) as s: return jsonify([serialize(x) for x in s.scalars(select(model).order_by(model.id))])
    @app.post('/venues')
    def new_venue():
        d=request.get_json() or {}
        name=text_value(d,'name',100); address=text_value(d,'address',200)
        with Session(engine) as s, s.begin():
            v=Venue(name=name,address=address)
            s.add(v); s.flush(); result=serialize(v)
        return jsonify(result),201
    @app.get('/courts')
    def courts():
        q=select(Court).order_by(Court.id)
        if request.args.get('sport'): q=q.where(Court.sport==request.args['sport'])
        if request.args.get('venue_id'): q=q.where(Court.venue_id==int(request.args['venue_id']))
        with Session(engine) as s: return jsonify([serialize(x) for x in s.scalars(q)])
    @app.post('/courts')
    def new_court():
        d=request.get_json() or {}
        price=Decimal(str(d['hourly_price']))
        if not price.is_finite() or price<0 or price>99999999: raise ValueError('Precio inválido')
        with Session(engine) as s, s.begin():
            venue=integer(d,'venue_id')
            if not s.get(Venue,venue): return jsonify(error='Sede inexistente'),404
            c=Court(venue_id=venue,name=text_value(d,'name',100),sport=text_value(d,'sport',40),capacity=integer(d,'capacity'),hourly_price=price)
            s.add(c); s.flush(); result=serialize(c)
        return jsonify(result),201
    @app.get('/courts/availability')
    def availability():
        d=request.args.to_dict(); d.setdefault('duration','60'); start,end=interval(d)
        with Session(engine) as s:
            return jsonify([serialize(c) for c in s.scalars(select(Court).order_by(Court.id)) if available(s,c.id,start,end) and (not d.get('sport') or c.sport==d['sport']) and (not d.get('venue_id') or c.venue_id==int(d['venue_id']))])
    @app.get('/courts/<int:id>')
    def detail(id):
        with Session(engine) as s:
            c=s.get(Court,id)
            if not c: return jsonify(error='Loza inexistente'),404
            return jsonify(**serialize(c),schedules=[serialize(w) for w in s.scalars(select(Schedule).where(Schedule.court_id==id))])
    @app.post('/courts/<int:id>/schedules')
    def schedule(id):
        d=request.get_json() or {}; day=integer(d,'weekday',0,6)
        start=time.fromisoformat(d['start_time']); end=time.fromisoformat(d['end_time'])
        if start.tzinfo or end.tzinfo or start>=end: raise ValueError('Horario inválido')
        with Session(engine) as s, s.begin():
            c=s.scalar(select(Court).where(Court.id==id).with_for_update())
            if not c: return jsonify(error='Loza inexistente'),404
            if s.scalar(select(Schedule.id).where(Schedule.court_id==id,Schedule.weekday==day,Schedule.start_time<end,Schedule.end_time>start)): return jsonify(error='Horario superpuesto'),409
            w=Schedule(court_id=id,weekday=day,start_time=start,end_time=end); s.add(w); s.flush(); result=serialize(w)
        return jsonify(result),201
    @app.post('/rentals')
    def rent():
        d=request.get_json() or {}; start,end=interval(d)
        with Session(engine) as s, s.begin():
            c=s.scalar(select(Court).where(Court.id==integer(d,'court_id')).with_for_update())
            if not c or not s.get(User,integer(d,'user_id')): return jsonify(error='Loza o usuario inexistente'),404
            sport=text_value(d,'sport',40)
            if sport!=c.sport: raise ValueError('Deporte incompatible con la loza')
            if not available(s,c.id,start,end): return jsonify(error='No disponible en ese horario'),409
            r=Rental(court_id=c.id,user_id=int(d['user_id']),event=text_value(d,'event',120),sport=sport,starts_at=start,ends_at=end,total=(c.hourly_price*Decimal(int(d['duration']))/60).quantize(Decimal('0.01')))
            s.add(r); s.flush(); result=serialize(r)
        return jsonify(result),201
    @app.post('/rentals/<int:id>/confirm')
    def confirm(id):
        d=request.get_json() or {}; payment=d.get('payment_status','pending')
        if payment not in ('pending','paid'): raise ValueError('Estado de pago inválido')
        with Session(engine) as s,s.begin():
            r=s.scalar(select(Rental).where(Rental.id==id).with_for_update())
            if not r: return jsonify(error='Reserva inexistente'),404
            if r.status=='cancelled': return jsonify(error='Reserva cancelada'),409
            r.status='confirmed'
            if r.payment_status!='paid': r.payment_status=payment
            s.flush(); result=serialize(r)
        return jsonify(result)
    @app.get('/users/<int:id>/rentals')
    @app.get('/courts/<int:id>/rentals')
    def history(id):
        by_user=request.path.startswith('/users')
        with Session(engine) as s:
            if not s.get(User if by_user else Court,id): return jsonify(error='No encontrado'),404
            q=select(Rental).where((Rental.user_id if by_user else Rental.court_id)==id).order_by(Rental.starts_at.desc())
            return jsonify([serialize(r) for r in s.scalars(q)])
    return app

app=create_app()
if __name__=='__main__': app.run(host='0.0.0.0',port=8000)
