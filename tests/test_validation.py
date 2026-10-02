from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
import pytest
from app import integer,interval,text_value

@pytest.mark.parametrize('value',[0,-1,721,True,60.5,'abc',None])
def test_invalid_duration(value):
    with pytest.raises((ValueError,TypeError)):
        integer({'duration':value},'duration',30,720)

@pytest.mark.parametrize('value',[30,60,720])
def test_duration_limits(value):
    assert integer({'duration':value},'duration',30,720)==value

def future_date():
    return (datetime.now(ZoneInfo('America/Lima'))+timedelta(days=2)).date().isoformat()

def test_duration_is_applied():
    start,end=interval({'date':future_date(),'time':'10:00','duration':90})
    assert end-start==timedelta(minutes=90)
    assert end.hour==11 and end.minute==30

def test_reject_midnight_crossing():
    with pytest.raises(ValueError,match='mismo día'):
        interval({'date':future_date(),'time':'23:30','duration':60})

def test_reject_timezone_in_local_time():
    with pytest.raises(ValueError,match='Lima'):
        interval({'date':future_date(),'time':'10:00+00:00','duration':60})

@pytest.mark.parametrize('value',['','   ','x'*121,None])
def test_event_is_required_and_limited(value):
    with pytest.raises(ValueError):text_value({'event':value},'event',120)
