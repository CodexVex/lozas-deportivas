# Registro y alquiler de lozas deportivas

Flask + SQLAlchemy (ORM) + PostgreSQL + HTML/JavaScript.

Aplicación publicada: https://lozas-codexvex-8bfb6baa.eastus.cloudapp.azure.com

Repositorio: https://github.com/CodexVex/lozas-deportivas

## Ejecutar en tu computadora

Abre Docker Desktop. Dentro de la carpeta del proyecto, copia y pega:

```bash
cp .env.example .env
docker compose up -d db
```

Cuando la base esté lista (`docker compose exec db pg_isready -U lozas -d lozas`), ejecuta:

```bash
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U lozas -d lozas < bd.sql
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U lozas -d lozas < feed.sql
docker compose up -d --build web
```

Abre http://localhost.

1. Consulta disponibilidad con fecha futura, hora, duración, deporte y sede.
2. Selecciona usuario y loza, escribe el evento y reserva.
3. En el historial puedes confirmar la reserva y registrar el pago.
4. Consulta historial por usuario o loza.
5. Registra una loza nueva y agrega sus horarios.

Pago manual y usuarios ficticios, sin inicio de sesión. Las horas son de Lima. Lunes=0 y domingo=6. Las solicitudes pendientes bloquean el horario; no se admiten solapamientos ni reservas que crucen medianoche.

## Base de datos

`bd.sql` crea cinco tablas en la base `lozas`, creada por Docker. `feed.sql` carga 10 sedes, 10 usuarios, 10 lozas, 70 horarios y 10 alquileres históricos. Se pueden ejecutar de nuevo sin borrar los datos. PostgreSQL usa un volumen persistente y no tiene puerto público.

## Automatizaciones de GitHub

En **Actions**, ejecuta en este orden y espera a que cada una termine:

| Archivo | Resultado |
|---|---|
| `infra.yml` | Terraform crea la máquina y la red en Azure; guarda el estado en Blob Storage |
| `setup.yml` | Ejecuta `bd.sql` y `feed.sql` en la máquina |
| `deploy.yml` | Publica la aplicación y muestra su URL |
| `generase-documentation.yml` | Genera diccionario y Mermaid; ejecuta las pruebas |

La última también se ejecuta con cada cambio a `main`. La documentación está en `docs/` y en el artefacto `diccionario-y-diagrama` de Actions. Las pruebas cubren reserva, validación, solapamiento, confirmación, historial y concurrencia con PostgreSQL.

Para ejecutar pruebas locales:

```bash
docker compose exec -T web python -m pytest -q
```

## Configuración de Azure

Requiere la suscripción **Azure for Students** activa. Se utiliza una sola VM pequeña para web y base de datos. Se apaga a las **23:00 de Lima**; se encenderá automáticamente a las 07:00 de Lima del 2 al 6 de octubre de 2026 para la revisión. Después puedes iniciar `vm-lozas` manualmente en Azure. Disco e IP pueden consumir crédito mientras está apagada.

GitHub necesita el secreto `AZURE_CREDENTIALS` y la variable `TF_STATE_ACCOUNT` (nombre único, solo minúsculas y números). La credencial tiene permiso Contributor únicamente en `rg-lozas-demo` y `rg-lozas-state`. No publiques su contenido.

Si necesitas configurar la credencial de nuevo, ejecuta en Azure Cloud Shell (Bash):

```bash
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
az group create -n rg-lozas-demo -l eastus
az group create -n rg-lozas-state -l eastus
az ad sp create-for-rbac --name lozas-github --role Contributor --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-lozas-demo" "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-lozas-state" --sdk-auth
```

Guarda el JSON devuelto en **Settings → Secrets and variables → Actions → Secrets → AZURE_CREDENTIALS**. En **Variables**, agrega `TF_STATE_ACCOUNT`, por ejemplo `lozasvex12345678`. La región predeterminada es `eastus`; puede cambiarse con `AZURE_LOCATION`.

La aplicación publicada usa el nombre público de Azure y HTTPS con Caddy. El certificado se renueva automáticamente. Se abren los puertos web 80 y 443; PostgreSQL sigue sin puerto público. La ejecución local sencilla continúa en http://localhost. `setup.yml` utiliza `psql`; Liquibase era opcional en el enunciado.

## API

- `POST /courts`, `GET /courts`, `GET /courts/{id}`.
- `POST /courts/{id}/schedules`.
- `GET /courts/availability?date=2026-12-10&time=10:00&duration=60`.
- `POST /rentals`, `POST /rentals/{id}/confirm`.
- `GET /users/{id}/rentals`, `GET /courts/{id}/rentals`.
- `GET /users`, `GET /venues`, `GET /health`.

Ejemplo (usa una fecha futura y confirma con el ID devuelto):

```bash
curl -X POST http://localhost/rentals -H 'Content-Type: application/json' -d '{"court_id":1,"user_id":1,"event":"Partido","sport":"Fútbol","date":"2026-12-10","time":"10:00","duration":60}'
curl -X POST http://localhost/rentals/11/confirm -H 'Content-Type: application/json' -d '{"payment_status":"paid"}'
```

Para detener localmente: `docker compose stop`. Para iniciar: `docker compose up -d`.

## Entrega

- Repositorio: https://github.com/CodexVex/lozas-deportivas (privado; comparte acceso con el docente).
- Aplicación publicada y verificada: https://lozas-codexvex-8bfb6baa.eastus.cloudapp.azure.com
- Diccionario y diagrama: `docs/diccionario.md`, `docs/diagrama.md`, `docs/er.mmd`.

Verificación: infraestructura, carga SQL y despliegue completados en GitHub Actions. 21 pruebas pasan con PostgreSQL (18 unitarias y 3 de integración); salud, página, lozas, disponibilidad e historial comprobados en la URL pública.

`startup.yml` programa cinco encendidos, del 2 al 6 de octubre de 2026, a las 07:00 de Lima. GitHub puede retrasar las ejecuciones programadas. El encendido automático no continúa después del 6; el apagado de las 23:00 se mantiene. El flujo también permite un encendido manual con Run workflow.
