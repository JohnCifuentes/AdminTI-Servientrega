# 09. Servicio de base de datos MySQL

**Proyecto:** Administración de Infraestructura de TI — Servientrega S.A. (entorno académico simulado)  
**Servicio:** MySQL 8.4 sobre Docker Swarm, administrado desde Dokploy  
**Documento:** `AdminTI/infraestructura/09-servicio-mysql.md`  
**Estado:** Instalación, configuración, autenticación, consultas SQL e integración técnica con Flask validadas.  
**Alcance:** Entorno de laboratorio; no representa infraestructura oficial de Servientrega S.A.

---

## 1. Objetivo

Implementar y verificar un servicio de base de datos relacional MySQL para almacenar los perfiles institucionales utilizados por el portal web simulado de la sede. El servicio debe ejecutarse en contenedor, disponer de persistencia, permanecer accesible por una red Docker privada y permitir consultas autenticadas desde la aplicación Flask sin publicar MySQL hacia la red del laboratorio.

## 2. Alcance y arquitectura

La solución se implementó en el servidor Ubuntu del laboratorio (`srv-servientrega`) mediante Docker y Dokploy. El servicio MySQL es independiente de la aplicación web: la base de datos se administra desde Dokploy y Flask consume sus datos mediante una conexión privada.

| Elemento | Configuración verificada |
|---|---|
| Servidor de infraestructura | `srv-servientrega` — Ubuntu Server |
| Plataforma de contenedores | Docker / Docker Swarm |
| Administrador de despliegues | Dokploy |
| Proyecto de Dokploy | `Servientrega` |
| Entorno de Dokploy | `production` |
| Servicio en Dokploy | `mysql-servientrega` |
| Nombre de aplicación | `servientrega-mysql` |
| Servicio Docker Swarm | `servientrega-mysql-do9ws9` |
| Imagen | `mysql:8.4` |
| Versión verificada por SQL | `8.4.13` |
| Base de datos | `servientrega_db` |
| Usuario de aplicación | `servientrega_app` |
| Puerto interno | `3306/tcp` |
| Red Docker | `dokploy-network` (`overlay`, ámbito `swarm`, `Attachable: true`) |
| Volumen persistente | `servientrega-mysql-do9ws9-data` |
| Punto de montaje | `/var/lib/mysql` |
| Réplicas | `1/1` |

**Esquema lógico:**

```text
Windows 11 (navegador)
        |
        | HTTP de laboratorio (portal de prueba)
        v
Portal Flask / Gunicorn (contenedor Docker)
        |
        | Red privada dokploy-network
        | DNS interno: servientrega-mysql-do9ws9
        | TCP 3306 / autenticación servientrega_app
        v
MySQL 8.4 (servicio Docker Swarm, Dokploy)
        |
        +-- Base: servientrega_db
        |      +-- Tabla: perfiles
        |
        +-- Volumen persistente: /var/lib/mysql
```

**Separación de responsabilidades:** el procedimiento de desarrollo, construcción y publicación del portal se documentará en `10-portal-web-flask.md`. Este documento se limita a la base de datos y a las pruebas necesarias para acreditar su integración.

## 3. Prerrequisitos

- Ubuntu Server operativo con acceso administrativo mediante SSH.
- Docker, Docker Swarm y Dokploy instalados y funcionando.
- Proyecto `Servientrega` y entorno `production` disponibles en Dokploy.
- Red `dokploy-network` existente.
- Acceso a la interfaz de Dokploy desde el laboratorio: `http://192.168.10.10:3000`.
- Credenciales de administración de Dokploy y contraseñas de MySQL custodiadas fuera del repositorio documental.

## 4. Despliegue del servicio en Dokploy

Desde el proyecto `Servientrega`, entorno `production`, se creó un recurso de base de datos MySQL con los siguientes parámetros:

| Parámetro | Valor |
|---|---|
| Nombre del recurso | `mysql-servientrega` |
| App Name | `servientrega-mysql` |
| Imagen | `mysql:8.4` |
| Database Name | `servientrega_db` |
| Database User | `servientrega_app` |
| Database Password | Secreto definido durante la creación; **no documentar el valor** |
| Root Password | Secreto independiente; **no documentar el valor** |
| Almacenamiento | Volumen `servientrega-mysql-do9ws9-data` en `/var/lib/mysql` |
| Red interna | `dokploy-network` |
| Puerto de servicio | `3306` (interno) |
| Réplicas | 1 |
| Límite de memoria | 1 GiB |
| Reserva de memoria | 256 MiB |
| Límite de CPU | 2 CPU |
| Reserva de CPU | 1 CPU |

Se ejecutó **Deploy** y Dokploy notificó que el despliegue había finalizado correctamente. La inspección posterior mostró el servicio con **1/1 réplicas** y el contenedor MySQL activo.

### 4.1. Exposición de red

La verificación real de Docker mostró `3306/tcp` como puerto del contenedor, **sin asignación de puerto en el host**. Además, una comprobación con `ss` no encontró un proceso escuchando en el puerto `3306` del servidor. Esto confirma la ausencia de publicación de ese puerto en el host durante las pruebas; no debe confundirse con un valor mostrado en el campo de puerto externo de la interfaz de Dokploy.

El nombre interno utilizado para las conexiones es `servientrega-mysql-do9ws9`. Se evita depender de la IP temporal del contenedor.

## 5. Comprobación de funcionamiento del servicio

### 5.1. Estado del servicio Swarm

```bash
sudo docker service ls --filter name=servientrega-mysql
```

**Resultado observado:** servicio `servientrega-mysql-do9ws9`, imagen `mysql:8.4`, estado `replicated 1/1`.

### 5.2. Contenedor y registros

```bash
sudo docker ps --filter "ancestor=mysql:8.4"

MYSQL_CONTAINER=$(sudo docker ps \
  --filter "ancestor=mysql:8.4" \
  --format '{{.ID}}' | head -n 1)

sudo docker logs --tail 25 "$MYSQL_CONTAINER"
```

Los registros confirmaron la creación de `servientrega_db`, la creación de `servientrega_app`, la concesión de acceso a la base y el mensaje **ready for connections**. La versión comprobada fue MySQL **8.4.13**.

Se observaron advertencias relativas al certificado interno autofirmado y al directorio del archivo PID. No se observaron errores que impidieran el inicio del servicio. Dichas advertencias no equivalen a una auditoría de seguridad completa.

### 5.3. Puerto en el host

```bash
sudo ss -lntp | grep ':3306 '
```

**Resultado observado:** sin coincidencias. La aplicación accede a MySQL por la red interna de Docker.

## 6. Acceso autenticado a la base de datos

Se utilizó el usuario de aplicación, sin recurrir a la cuenta `root` para las operaciones habituales:

```bash
MYSQL_CONTAINER=$(sudo docker ps \
  --filter "ancestor=mysql:8.4" \
  --format '{{.ID}}' | head -n 1)

sudo docker exec -it "$MYSQL_CONTAINER" \
  mysql --default-character-set=utf8mb4 \
  -u servientrega_app -p servientrega_db
```

La opción `-p` solicita la contraseña interactivamente, evitando escribirla en el comando.

Consultas de validación ejecutadas:

```sql
SELECT DATABASE() AS base_datos_actual;
SELECT CURRENT_USER() AS usuario_autenticado;
SELECT VERSION() AS version_mysql;
```

| Consulta | Resultado real |
|---|---|
| `DATABASE()` | `servientrega_db` |
| `CURRENT_USER()` | `servientrega_app@%` |
| `VERSION()` | `8.4.13` |

Estas pruebas acreditan autenticación y acceso a la base indicada.

## 7. Modelo de datos

Para mantener el alcance de la aplicación web académica, se implementó una única tabla de perfiles institucionales. No se desarrollaron módulos de registro, seguimiento ni consulta de envíos.

### 7.1. Definición de tabla

```sql
CREATE TABLE IF NOT EXISTS perfiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(60) NOT NULL,
    mensaje TEXT NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);
```

| Campo | Tipo | Propósito |
|---|---|---|
| `id` | `INT AUTO_INCREMENT` | Identificador primario |
| `codigo` | `VARCHAR(30)` | Identificador único del perfil |
| `nombre` | `VARCHAR(60)` | Nombre visible del perfil |
| `mensaje` | `TEXT` | Mensaje institucional mostrado en el portal |
| `activo` | `BOOLEAN` | Indicador de disponibilidad del perfil |

### 7.2. Registros incorporados

Se crearon dos registros:

| ID observado | Código | Nombre | Activo |
|---|---|---|---|
| 1 | `administrador` | Administrador | 1 |
| 2 | `operador` | Operador | 1 |

Mensajes finales verificados:

- **Administrador:** «Bienvenido al panel administrativo. Desde este perfil se supervisa la infraestructura tecnológica de la sede.»
- **Operador:** «Bienvenido al área operativa. Desde este perfil se apoyan las actividades diarias de la sede.»

Consultas de comprobación:

```sql
SHOW TABLES;

SELECT id, codigo, nombre, activo
FROM perfiles
ORDER BY id;

SELECT codigo, nombre, mensaje
FROM perfiles
ORDER BY id;
```

**Resultados observados:** una tabla (`perfiles`) y dos registros activos, con sus mensajes completos.

## 8. Incidencias y acciones correctivas

### 8.1. Caracteres acentuados omitidos al insertar datos

Durante la inserción inicial se observaron textos incompletos (`tecnolgica` y `rea`). Se corrigieron los dos mensajes con `UPDATE` y `CHAR(... USING utf8mb4)` para evitar problemas al pegar caracteres especiales desde la terminal.

```sql
UPDATE perfiles
SET mensaje = CONCAT(
    'Bienvenido al panel administrativo. ',
    'Desde este perfil se supervisa la infraestructura tecnol',
    CHAR(195, 179 USING utf8mb4),
    'gica de la sede.'
)
WHERE codigo = 'administrador';

UPDATE perfiles
SET mensaje = CONCAT(
    'Bienvenido al ',
    CHAR(195, 161 USING utf8mb4),
    'rea operativa. ',
    'Desde este perfil se apoyan las actividades diarias de la sede.'
)
WHERE codigo = 'operador';
```

Ambas actualizaciones reportaron **1 fila modificada y 0 advertencias**. La consulta posterior mostró `tecnológica` y `área` correctamente.

### 8.2. Advertencias de inserción

La sentencia inicial `INSERT ... ON DUPLICATE KEY UPDATE` generó dos advertencias. No se consultó `SHOW WARNINGS` en esa sesión, por lo que no se determinó de forma concluyente su causa. El resultado final de los datos sí fue validado. Para futuras inserciones conviene evitar sintaxis obsoletas y revisar las advertencias cuando aparezcan.

## 9. Integración comprobada con el portal Flask

### 9.1. Redes Docker

La inspección mostró:

- Portal Flask inicial: red `bridge`.
- Contenedor MySQL: red `dokploy-network`.
- `dokploy-network`: controlador `overlay`, ámbito `swarm`, propiedad `Attachable: true`.

El contenedor inicial de Flask fue conectado a la red privada mediante:

```bash
sudo docker network connect dokploy-network portal-servientrega
```

La inspección posterior confirmó que el portal conservaba `bridge` y había incorporado `dokploy-network`. La ruta `/health` continuó respondiendo HTTP 200.

**Nota operativa:** esta conexión manual puede perderse si el contenedor se elimina y se recrea. El despliegue definitivo debe declarar la red apropiada desde Dokploy.

### 9.2. Resolución DNS y conectividad TCP

Desde el contenedor Flask se ejecutaron pruebas con `socket.gethostbyname()` y `socket.create_connection()` hacia `servientrega-mysql-do9ws9:3306`.

**Resultados reales:**

- DNS interno correcto: `servientrega-mysql-do9ws9` resolvió a `10.0.1.8` durante la prueba.
- Conectividad TCP al puerto `3306`: correcta.

La IP `10.0.1.8` es un dato de diagnóstico puntual, no una dirección que deba fijarse en el código.

### 9.3. Credenciales de aplicación

El portal utiliza las variables:

```text
DB_HOST=servientrega-mysql-do9ws9
DB_PORT=3306
DB_NAME=servientrega_db
DB_USER=servientrega_app
DB_PASSWORD=[valor secreto, no documentado]
```

En el entorno de prueba se almacenaron en un archivo `.env` con permisos `0600`, excluido de la imagen mediante `.dockerignore`. **No se incorpora el archivo ni su contraseña al documento.** Para el despliegue definitivo, las variables deben configurarse en el entorno de Dokploy con acceso restringido.

### 9.4. Pruebas HTTP de integración

Se construyó la imagen `portal-servientrega:2.0` con Flask 3.1.1, Gunicorn 23.0.0 y PyMySQL 1.1.1. Se inició un contenedor de prueba `portal-servientrega-test` en `dokploy-network`, publicado únicamente en la IP de laboratorio `192.168.10.10`, puerto `5001`.

| Prueba | Resultado observado | Interpretación |
|---|---|---|
| `GET /health` | HTTP 200 | Flask/Gunicorn operativo |
| `GET /health/db` | HTTP 200, `{"database":"connected","status":"ok"}` | Conexión autenticada y ejecución de `SELECT 1` |
| `GET /?rol=administrador` | HTTP 200 | Consulta del perfil y renderización completadas |
| `GET /?rol=operador` | HTTP 200 | Consulta del perfil y renderización completadas |

La implementación de Flask ejecuta una consulta parametrizada sobre `perfiles`, filtrando por `codigo` y `activo = 1`. Estas pruebas permiten **dar por validada la integración técnica Flask–MySQL**. La revisión visual del portal de prueba desde Windows y el despliegue definitivo con HTTPS pertenecen al cierre del servicio 10.

## 10. Seguridad y operación

### 10.1. Medidas aplicadas

- Usuario de aplicación `servientrega_app`, distinto de `root`.
- Contraseñas ingresadas de manera interactiva en la consola MySQL.
- Servicio accesible por red Docker privada; no se observó publicación del puerto 3306 en el host.
- Contraseña de Flask fuera del código fuente, mediante variables de entorno.
- Archivo `.env` de prueba protegido con permisos `0600` y excluido del contexto de imagen Docker.
- Consultas parametrizadas en Flask, sin concatenar el valor de `rol` dentro del SQL.
- Volumen persistente para los datos de MySQL.

### 10.2. Limitaciones y precauciones

- La existencia de un volumen persistente **no sustituye una copia de seguridad**. No se ha documentado ni validado una restauración de respaldo.
- No se realizó una auditoría completa de permisos SQL, certificados TLS de MySQL ni endurecimiento del contenedor.
- El valor `servientrega_app@%` indica que el usuario puede autenticarse desde distintos orígenes permitidos por la conectividad y las políticas del servidor; el aislamiento efectivo depende también de la red Docker y de los controles de acceso.
- Los perfiles del portal son demostrativos: **no constituyen autenticación ni autorización de usuarios reales**.
- El despliegue definitivo del portal en Dokploy y HTTPS está pendiente y se documentará por separado.

### 10.3. Verificaciones de mantenimiento

```bash
# Estado del servicio.
sudo docker service ls --filter name=servientrega-mysql

# Contenedor activo.
sudo docker ps --filter 'ancestor=mysql:8.4'

# Registros recientes.
MYSQL_CONTAINER=$(sudo docker ps \
  --filter 'ancestor=mysql:8.4' \
  --format '{{.ID}}' | head -n 1)
sudo docker logs --tail 50 "$MYSQL_CONTAINER"

# Confirmar ausencia de publicación del puerto en el host.
sudo ss -lntp | grep ':3306 '
```

Si `ss` no devuelve coincidencias, no se detecta escucha local del puerto 3306 en ese momento. Antes de cualquier cambio de imagen, credenciales o almacenamiento, se recomienda preparar un respaldo verificable y planificar la ventana de mantenimiento.

## 11. Evidencias

Las capturas se almacenan en `AdminTI/capturas/`, conservando la numeración consecutiva del proyecto.

| Evidencia | Archivo | Contenido |
|---|---|---|
| 30 | `30-mysql-validacion-consultas.png` | Sesión MySQL autenticada: base, usuario y versión |
| 31 | `31-mysql-servicio-activo-dokploy.png` | Estado activo del servicio MySQL en Dokploy, con credenciales ocultas |
| 32 | `32-portal-flask-mysql-integracion.png` | **Propuesta pendiente de confirmar:** validación visual del portal Flask 2.0 conectado a MySQL; corresponde principalmente al documento 10 |

Las capturas 30 y 31 fueron designadas como evidencias del servicio; su ubicación física debe confirmarse en el repositorio antes de la entrega. La captura 32 no se considera realizada hasta que se confirme su guardado.

## 12. Criterios de aceptación y cierre

| Criterio | Estado |
|---|---|
| MySQL desplegado desde Dokploy | Cumplido |
| Servicio Docker Swarm operativo (1/1) | Cumplido |
| Persistencia configurada | Cumplido (configuración, no prueba de restauración) |
| Base y usuario de aplicación creados | Cumplido |
| Tabla y dos perfiles almacenados | Cumplido |
| Lecturas SQL autenticadas | Cumplido |
| Conectividad privada desde Flask | Cumplido |
| Consulta autenticada desde Flask | Cumplido |
| Consulta de perfiles desde Flask | Cumplido |
| Despliegue definitivo del portal y HTTPS | Pendiente; alcance del documento 10 |

**Conclusión:** el servicio de base de datos MySQL queda **configurado y validado funcionalmente** para el entorno académico. El servicio proporciona almacenamiento persistente configurado, acceso autenticado y datos consumidos por el portal Flask de prueba. El despliegue final de la aplicación, la publicación HTTPS y la documentación de la interfaz se gestionan en `10-portal-web-flask.md`.
