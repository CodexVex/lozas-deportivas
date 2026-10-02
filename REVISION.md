# Revisión breve

## Pruebas

- Unitarias: duración y límites, fecha pasada, medianoche, zona horaria y evento obligatorio.
- Integración: reserva, importe, conflictos, confirmación, pago, historial y validación con PostgreSQL.
- Concurrencia: dos solicitudes al mismo horario; solo una debe aceptarse.
- SQL: creación y carga de al menos 10 registros por tabla.

Resultado: 18 pruebas unitarias y 3 de integración pasan con PostgreSQL, incluidas solicitudes concurrentes. Se verificaron además la página, la salud de la aplicación, disponibilidad e historial en la URL pública. La evidencia está en GitHub Actions. Las pruebas no cubren cada formulario ni fallos de red o recuperación tras una caída.

## Límites del código y la arquitectura

- Sin autenticación ni permisos: cualquier visitante puede reservar, consultar historiales y registrar pagos. Usa solo datos ficticios.
- El pago es manual; no hay pasarela ni verificación bancaria.
- Las reservas pendientes no expiran y no existe un flujo de cancelación en la pantalla.
- Una sola VM: si falla, se detienen web y base de datos. No hay copias de seguridad automáticas.
- La demo publica por HTTP; no incluye HTTPS.
- SQL y modelos ORM se mantienen manualmente, sin migraciones de esquema.
- La capacidad se muestra, pero no se valida contra asistentes de un evento.
- Si una reserva cruza dos franjas contiguas configuradas por separado, la validación actual la rechaza. Los horarios de ejemplo usan una única franja diaria.

## Respecto al enunciado

- Se usa Flask y HTML sencillo. El enunciado permite otro framework; no se implementó .NET ni React/Angular/Vue.
- Los horarios son semanales, pero la búsqueda consulta una fecha concreta; no hay calendario semanal visual.
- Administración mínima: registro de lozas y horarios, sin edición ni eliminación desde la pantalla.
- Liquibase era una sugerencia: `setup.yml` utiliza `psql` y los dos archivos SQL.
- Treinta minutos permiten una demostración básica. Autenticación, pagos reales, seguridad y recuperación requieren más trabajo. El aprovisionamiento también depende de Azure.

## Consideraciones evaluables

| Consideración | Estado | Evidencia |
|---|---|---|
| Framework, validación y GitHub | Cumple con alternativa permitida | Flask, formularios HTML y validaciones de API; repositorio GitHub |
| ORM | Cumple | SQLAlchemy para consultas y escrituras |
| bd.sql y feed.sql, mínimo 10 registros por tabla | Cumple | 10 sedes, 10 usuarios, 10 lozas, 70 horarios y 10 alquileres |
| infra.yml con Terraform | Cumple | Infraestructura aprovisionada y flujo ejecutado correctamente |
| setup.yml para ejecutar SQL | Cumple | Carga verificada en Azure con psql; Liquibase era sugerido |
| deploy.yml | Cumple | Aplicación publicada y comprobada |
| generase-documentation.yml | Cumple | Diccionario de datos y Mermaid generados desde PostgreSQL |

Se entregan la URL de la aplicación y del repositorio. El repositorio es privado: el evaluador necesita acceso. Estas consideraciones están cubiertas, pero el alcance funcional completo y la preparación para producción conservan los límites descritos arriba.
