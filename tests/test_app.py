import os
from datetime import datetime,timedelta
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import Base,Venue,User,Court,Schedule,Rental,create_app,interval

@pytest.fixture
def client(tmp_path):
    url=os.environ.get('TEST_DATABASE_URL',f'sqlite:///{tmp_path}/test.db')
    app=create_app(url); engine=app.config['ENGINE']
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
    with Session(engine) as s,s.begin():
        s.add_all([Venue(id=1,name='Sede',address='Av. 1'),User(id=1,name='Ana',email='ana@example.com')]);s.flush()
        s.add(Court(id=1,venue_id=1,name='Loza',sport='Fútbol',capacity=20,hourly_price=30));s.flush()
        from datetime import time
        for d in range(7): s.add(Schedule(court_id=1,weekday=d,start_time=time(8),end_time=time(22)))
    yield app.test_client()
    engine.dispose()
def payload(**kw):
    d=dict(court_id=1,user_id=1,event='Partido',sport='Fútbol',date=(datetime.now()+timedelta(days=2)).date().isoformat(),time='10:00',duration=60)
    return d|kw

def test_interval_rejects_past():
    with pytest.raises(ValueError):interval({'date':'2020-01-01','time':'10:00','duration':60})
def test_complete_flow_and_overlap(client):
    r=client.post('/rentals',json=payload());assert r.status_code==201;id=r.json['id'];assert r.json['total']==30
    assert client.post('/rentals',json=payload(time='10:30')).status_code==409
    assert client.post('/rentals',json=payload(time='11:00')).status_code==201
    assert client.post(f'/rentals/{id}/confirm',json={'payment_status':'paid'}).json['payment_status']=='paid'
    assert len(client.get('/users/1/rentals').json)==2
    assert len(client.get('/courts/1/rentals').json)==2
    assert client.get('/courts/availability',query_string=payload()).json==[]
def test_validation(client):
    assert client.post('/rentals',json=payload(time='07:00')).status_code==409
    assert client.post('/rentals',json=payload(sport='Vóley')).status_code==400
    assert client.post('/rentals',json=payload(duration=-1)).status_code==400
    assert client.post('/rentals',json=payload(user_id=999)).status_code==404
    assert client.post('/courts',json={'venue_id':1,'name':'','sport':'Fútbol','capacity':0,'hourly_price':30}).status_code==400
    assert client.post('/courts/1/schedules',json={'weekday':0,'start_time':'09:00','end_time':'12:00'}).status_code==409
