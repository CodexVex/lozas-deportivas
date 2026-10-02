# Sistema de registro y alquiler de lozas deportivas

Proyecto académico mínimo: Flask + SQLAlchemy (ORM) + PostgreSQL 16 + HTML/JavaScript. El enunciado permite utilizar otro framework. No requiere Node ni .NET.

Repositorio: https://github.com/CodexVex/lozas-deportivas

## 1. Base de datos (5 minutos)

Instala y abre Docker Desktop. Desde la carpeta del proyecto ejecuta:

```bash
cp .env.example .env
docker compose up -d db
```

Espera a que PostgreSQL esté listo:

```bash
docker compose exec db pg_isready -U lozas -d lozas
```

Crea las tablas y carga los ejemplos, en este orden:

```bash
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U lozas -d lozas < bd.sql
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U lozas -d lozas < feed.sql
```

Las cinco tablas son `venues` (sedes), `users` (usuarios de demostración), `courts` (lozas), `schedules` (horarios por día) y `rentals` (reservas/alquileres y estado de pago). Hay 10 registros por tabla, excepto horarios, que contiene 70. Los ejemplos del historial son de enero de 2026 para no bloquear reservas futuras. Lunes=0 y domingo=6. Los scripts son repetibles; no borran tablas existentes. `bd.sql` crea la estructura dentro de la base `lozas`, creada por Docker.

## 2. Ejecutar aplicación (5 minutos)

```bash
docker compose up -d --build web
```

Abre http://localhost. No expone PostgreSQL al exterior. Su volumen conserva la información al reiniciar los contenedores.

1. Selecciona fecha futura, hora, deporte y sede. Pulsa **Consultar**.
2. Elige usuario y loza, escribe el evento y pulsa **Reservar horario consultado**.
3. Pulsa **Ver historial**. Puedes **Confirmar** y **Registrar pago**.
4. Consulta el historial por usuario o por loza.
5. Para registrar otra loza, completa el formulario y agrega al menos un horario semanal.

El importe se calcula por minutos. Las solicitudes pendientes también bloquean el horario. Una reserva contigua al final de otra está permitida. La transacción bloquea la fila de la loza en PostgreSQL para serializar solicitudes concurrentes. La validación se ejecuta en frontend y backend. Todos los horarios se interpretan en Lima, sin reservas que crucen medianoche.

Esta demostración permite seleccionar usuarios de ejemplo, sin autenticación ni pagos bancarios: **Registrar pago** actualiza un estado manual. Usa datos ficticios.

## 3. Pruebas y documentación

La automatización `generase-documentation.yml` se ejecuta al subir cambios a `main` o manualmente. Crea PostgreSQL, ejecuta ambos SQL, comprueba los recuentos y genera documentación desde el esquema real. Ejecuta pruebas unitarias e integración con PostgreSQL. En GitHub abre **Actions → generase-documentation → ejecución → Artifacts → diccionario-y-diagrama**.

También puedes ejecutarlo localmente:

```bash
docker compose exec -T web python scripts/documentation.py
docker compose cp web:/app/docs/. docs/
docker compose exec -T web python -m pytest -q
```

## 4. Publicar en Azure (depende del acceso y aprovisionamiento)

Requiere una suscripción activa con permiso para crear recursos. Una VM y almacenamiento consumen crédito o generan cargos según tu suscripción. El tiempo depende de Azure, de sus cuotas y del acceso a la cuenta; no se garantiza terminar la publicación en 30 minutos si falta esta configuración.

El repositorio incluye los cuatro archivos solicitados en `.github/workflows/`: `infra.yml`, `setup.yml`, `deploy.yml` y `generase-documentation.yml`.

### Preparar credencial de automatización

Abre Azure Cloud Shell en modo Bash y selecciona la suscripción correcta. Copia y pega:

```bash
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
az group create -n rg-lozas-demo -l eastus
az group create -n rg-lozas-state -l eastus
az ad sp create-for-rbac --name lozas-github --role Contributor --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-lozas-demo" "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-lozas-state" --sdk-auth
```

Copia el JSON devuelto directamente a **GitHub → repositorio → Settings → Secrets and variables → Actions → New repository secret** con el nombre `AZURE_CREDENTIALS`. No lo pegues en archivos del repositorio. Este paso crea una identidad de automatización con permisos solo en los dos grupos del proyecto; requiere que tu cuenta esté autorizada para ello.

En **Variables**, agrega `TF_STATE_ACCOUNT` con un nombre globalmente único, por ejemplo `lozasvex` seguido de 8 números, solo letras minúsculas y números, entre 3 y 24 caracteres. Opcional: `AZURE_LOCATION`, por defecto `eastus`.

### Ejecutar automatizaciones

1. **Actions → infra → Run workflow**. Espera el resultado correcto. Terraform aprovisiona una VM Ubuntu, red, IP pública y un volumen de sistema. Conserva su estado en Azure Blob Storage. El grupo y almacenamiento del estado se preparan antes de Terraform.
2. **Actions → setup → Run workflow**. Espera el resultado correcto. Envía los archivos del repositorio privado a la VM y ejecuta `bd.sql` y `feed.sql` con `psql` y detención ante errores. El uso de Liquibase era una sugerencia, no un requisito.
3. **Actions → deploy → Run workflow**. Construye y ejecuta la aplicación. Comprueba `/health` desde la IP pública.
4. Copia la URL `http://IP_PUBLICA` que aparece en el resumen de **deploy**. Esa es la URL final para la entrega, una vez comprobada.

El envío de archivos se realiza mediante Azure Run Command; no requiere abrir SSH ni publicar el repositorio. La contraseña de PostgreSQL se genera en la VM, y solo se abre el puerto web 80. El despliegue conserva el volumen de PostgreSQL. La VM ofrece HTTP para esta demostración; no incluye dominio ni HTTPS.

## API

| Método | Ruta | Función |
|---|---|---|
| POST | /courts | Registrar loza |
| GET | /courts?sport=Fútbol&venue_id=1 | Listar con filtros |
| GET | /courts/{id} | Detalle y horarios |
| POST | /courts/{id}/schedules | Agregar franja semanal |
| GET | /courts/availability?date=2026-12-10&time=10:00&duration=60 | Disponibilidad en fecha concreta conforme al horario semanal |
| POST | /rentals | Solicitar reserva |
| POST | /rentals/{id}/confirm | Confirmar y registrar pago |
| GET | /users/{id}/rentals | Historial por usuario |
| GET | /courts/{id}/rentals | Historial por loza |
| GET | /users | Usuarios de ejemplo |
| GET | /venues | Sedes de ejemplo |
| GET | /health | Estado de aplicación y acceso a tablas |

Ejemplo para copiar y pegar (ajusta la fecha para que sea futura):

```bash
curl -X POST http://localhost/rentals -H 'Content-Type: application/json' -d '{"court_id":1,"user_id":1,"event":"Partido amistoso","sport":"Fútbol","date":"2026-12-10","time":"10:00","duration":60}'
curl -X POST http://localhost/rentals/11/confirm -H 'Content-Type: application/json' -d '{"payment_status":"paid"}'
curl http://localhost/users/1/rentals
```

## Detener la demostración local

```bash
docker compose stop
```

Para volver a arrancar: `docker compose up -d`. No uses `down -v` si quieres conservar los datos.

## Entrega

- Repositorio: https://github.com/CodexVex/lozas-deportivas (privado; da acceso al docente si lo necesita).
- Aplicación publicada: pendiente hasta ejecutar y verificar el despliegue en Azure. Consulta el resumen de `deploy`.
- Diccionario: `docs/diccionario.md`.
- Diagrama Mermaid: `docs/er.mmd` y `docs/diagrama.md`.

La máquina se apaga automáticamente a las 23:00 de Lima. Para volver a usarla, inicia `vm-lozas` desde Azure. El disco y la IP conservados pueden seguir consumiendo crédito cuando está apagada.
