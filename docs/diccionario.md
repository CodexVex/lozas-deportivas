# Diccionario de datos

Generado automáticamente desde la base de datos.

## venues

| Campo | Tipo | Nulo | Clave |
|---|---|---|---|
| id | INTEGER | No | PK |
| name | VARCHAR(100) | No |  |
| address | VARCHAR(200) | No |  |

## courts

| Campo | Tipo | Nulo | Clave |
|---|---|---|---|
| id | INTEGER | No | PK |
| venue_id | INTEGER | No | FK |
| name | VARCHAR(100) | No |  |
| sport | VARCHAR(40) | No |  |
| capacity | INTEGER | No |  |
| hourly_price | NUMERIC(10, 2) | No |  |

## schedules

| Campo | Tipo | Nulo | Clave |
|---|---|---|---|
| id | INTEGER | No | PK |
| court_id | INTEGER | No | FK |
| weekday | INTEGER | No |  |
| start_time | TIME | No |  |
| end_time | TIME | No |  |

## rentals

| Campo | Tipo | Nulo | Clave |
|---|---|---|---|
| id | INTEGER | No | PK |
| court_id | INTEGER | No | FK |
| user_id | INTEGER | No | FK |
| event | VARCHAR(120) | No |  |
| sport | VARCHAR(40) | No |  |
| starts_at | TIMESTAMP | No |  |
| ends_at | TIMESTAMP | No |  |
| status | VARCHAR(20) | No |  |
| payment_status | VARCHAR(20) | No |  |
| total | NUMERIC(10, 2) | No |  |

## users

| Campo | Tipo | Nulo | Clave |
|---|---|---|---|
| id | INTEGER | No | PK |
| name | VARCHAR(100) | No |  |
| email | VARCHAR(150) | No |  |

