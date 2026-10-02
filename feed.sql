BEGIN;
INSERT INTO venues(id,name,address)
SELECT i, 'Sede ' || i, 'Av. Deportiva ' || i FROM generate_series(1,10) i
ON CONFLICT(id) DO NOTHING;
INSERT INTO users(id,name,email)
SELECT i, 'Usuario ' || i, 'usuario' || i || '@example.com' FROM generate_series(1,10) i
ON CONFLICT DO NOTHING;
INSERT INTO courts(id,venue_id,name,sport,capacity,hourly_price)
SELECT i,i,'Loza ' || i,CASE WHEN i%2=0 THEN 'Vóley' ELSE 'Fútbol' END,20,30+i
FROM generate_series(1,10) i ON CONFLICT(id) DO NOTHING;
INSERT INTO schedules(id,court_id,weekday,start_time,end_time)
SELECT (c-1)*7+d+1,c,d,'08:00'::time,'22:00'::time
FROM generate_series(1,10) c CROSS JOIN generate_series(0,6) d
ON CONFLICT DO NOTHING;
INSERT INTO rentals(id,court_id,user_id,event,sport,starts_at,ends_at,status,payment_status,total)
SELECT i,i,i,'Evento de ejemplo ' || i,CASE WHEN i%2=0 THEN 'Vóley' ELSE 'Fútbol' END,
TIMESTAMP '2026-01-05 10:00',TIMESTAMP '2026-01-05 11:00','confirmed','paid',30+i
FROM generate_series(1,10) i ON CONFLICT(id) DO NOTHING;
SELECT setval(pg_get_serial_sequence('venues','id'),(SELECT max(id) FROM venues));
SELECT setval(pg_get_serial_sequence('users','id'),(SELECT max(id) FROM users));
SELECT setval(pg_get_serial_sequence('courts','id'),(SELECT max(id) FROM courts));
SELECT setval(pg_get_serial_sequence('schedules','id'),(SELECT max(id) FROM schedules));
SELECT setval(pg_get_serial_sequence('rentals','id'),(SELECT max(id) FROM rentals));
COMMIT;
