# 10. Portal web Flask — Aplicación institucional simulada

**Proyecto:** Administración de Infraestructura de TI — Servientrega S.A. (entorno académico simulado)  
**Documento:** `AdminTI/infraestructura/10-portal-web-flask.md`  
**Servidor:** `srv-servientrega` — Ubuntu Server 24.04 LTS — IP Host-only `192.168.10.10`  
**Estado:** Aplicación Flask 2.0 desplegada como contenedor Docker independiente; conexión MySQL y acceso desde Windows validados.  
**Alcance:** Demostración académica; no es un sistema corporativo oficial ni una aplicación de gestión real de envíos.

---

## 1. Objetivo

Implementar un portal web institucional sencillo, accesible desde un cliente Windows en la red privada del laboratorio, que muestre información diferenciada para los perfiles **Administrador** y **Operador**. La aplicación debe ejecutarse en un contenedor Docker, servir HTML y CSS mediante Flask y Gunicorn, y obtener los mensajes de ambos perfiles desde una base de datos MySQL, demostrando la integración efectiva entre servicios de infraestructura.

El proyecto se centra en la **administración de infraestructura de TI**. No contempla registro de envíos, autenticación real, autorización por roles ni desarrollo de una plataforma logística completa.

## 2. Arquitectura y componentes

| Elemento | Configuración implementada |
|---|---|
| Servidor | `srv-servientrega`, Ubuntu Server 24.04 LTS |
| IP de acceso del laboratorio | `192.168.10.10` |
| Cliente de validación | Windows 11, navegador web |
| Lenguaje y framework | Python 3.12 / Flask 3.1.1 |
| Servidor de aplicación | Gunicorn 23.0.0 |
| Controlador de base de datos | PyMySQL 1.1.1 |
| Imagen base | `python:3.12-slim` |
| Imagen inicial | `portal-servientrega:1.0` |
| Imagen integrada | `portal-servientrega:2.0` |
| Contenedor original | `portal-servientrega` |
| Contenedor integrado de prueba | `portal-servientrega-test` |
| Acceso a versión 1.0 | `http://192.168.10.10:5000/` |
| Acceso a versión 2.0 | `http://192.168.10.10:5001/` |
| Base de datos | `servientrega_db`, tabla `perfiles` |
| Servicio MySQL | `servientrega-mysql-do9ws9`, puerto interno `3306` |
| Red compartida con MySQL | `dokploy-network` (Docker Swarm overlay) |
| Gestión del contenedor web | Docker CLI, **no** aplicación registrada en Dokploy |
| Protocolo de acceso web | HTTP; **HTTPS no configurado** |

**Diagrama lógico de la implementación validada:**

```text
Windows 11 — navegador
    |
    | HTTP / red Host-only 192.168.10.0/24
    v
Ubuntu Server — 192.168.10.10
    |
    +-- :5000 --> portal-servientrega (imagen 1.0)
    |                 Flask/Gunicorn; mensajes definidos en Python
    |
    +-- :5001 --> portal-servientrega-test (imagen 2.0)
                      Flask/Gunicorn + PyMySQL
                            |
                            | dokploy-network (red privada)
                            | DNS: servientrega-mysql-do9ws9
                            | TCP 3306
                            v
                      MySQL 8.4 / Dokploy
                      servientrega_db
                        +-- perfiles
```

**Separación de responsabilidades:** la instalación, configuración, persistencia, cuentas y validaciones propias de MySQL están documentadas en `09-servicio-mysql.md`. Aquí se documenta el consumo de esa base desde Flask y el funcionamiento del portal.

## 3. Prerrequisitos

- Servidor Ubuntu operativo y accesible mediante SSH con el usuario administrativo `adminserv`.
- Docker instalado y con capacidad para construir y ejecutar imágenes.
- Red Host-only configurada, con acceso desde Windows a `192.168.10.10`.
- MySQL 8.4 desplegado en Dokploy, base `servientrega_db`, usuario `servientrega_app` y tabla `perfiles` con dos registros activos.
- Red `dokploy-network` disponible y conectividad DNS/TCP entre el contenedor Flask y MySQL.
- Contraseña del usuario MySQL disponible para configurarla de forma local y confidencial; no se incorpora a la documentación.

## 4. Estructura del proyecto

La aplicación se desarrolló en:

```text
/home/adminserv/portal-servientrega/
├── app.py
├── app.py.bak             # Respaldo de la versión original
├── Dockerfile
├── requirements.txt
├── .dockerignore
├── .env                   # Credenciales locales, no incluir en imagen
├── templates/
│   └── index.html
└── static/
    └── css/
        └── styles.css
```

La carpeta de entrega del proyecto contempla `AdminTI/codigo/` para conservar el código fuente del portal. La ruta indicada arriba es la ubicación **real de ejecución** en Ubuntu; no se ha verificado una copia de estos archivos en `AdminTI/codigo/`.

### 4.1. Función de los archivos

| Archivo | Propósito |
|---|---|
| `app.py` | Rutas Flask, consulta de perfiles, renderizado y comprobaciones de salud |
| `templates/index.html` | Plantilla HTML/Jinja2 con selector de perfiles |
| `static/css/styles.css` | Estilos institucionales y diseño adaptable |
| `requirements.txt` | Dependencias Python con versiones fijadas |
| `Dockerfile` | Construcción de imagen y ejecución mediante Gunicorn |
| `.dockerignore` | Exclusión de archivos innecesarios y confidenciales |
| `.env` | Variables de conexión a MySQL para ejecución local |
| `app.py.bak` | Copia de seguridad del código anterior a la integración |

## 5. Implementación inicial del portal — versión 1.0

Se implementó una aplicación Flask que atendía peticiones `GET /`, interpretaba el parámetro `rol` y mostraba mensajes diferenciados para los perfiles `administrador` y `operador`. Los mensajes estaban inicialmente definidos en una estructura Python, sin conexión a base de datos.

La interfaz incluye botones de selección de perfil, encabezado institucional, contenido dinámico mediante Jinja2 y hoja de estilos CSS adaptable. Los perfiles son **opciones de visualización**, no sesiones autenticadas ni controles de acceso.

Se añadió la ruta `GET /health` para verificar que el proceso web responde.

### 5.1. Dependencias iniciales

```text
Flask==3.1.1
gunicorn==23.0.0
```

### 5.2. Dockerfile utilizado

El proyecto utiliza una imagen Python reducida, instala dependencias, copia código, plantillas y recursos estáticos, crea un usuario de aplicación sin privilegios y ejecuta Gunicorn:

```dockerfile
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY templates/ templates/
COPY static/ static/
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
```

La configuración de un trabajador y dos hilos responde al tamaño reducido del laboratorio; no se presenta como dimensionamiento de producción.

### 5.3. Construcción y ejecución inicial

Desde `/home/adminserv/portal-servientrega`:

```bash
sudo docker build --tag portal-servientrega:1.0 .

sudo docker run -d \
  --name portal-servientrega \
  --restart unless-stopped \
  --publish 192.168.10.10:5000:5000 \
  portal-servientrega:1.0
```

Se verificó que `GET /health` y la página principal respondían con **HTTP 200**. El usuario abrió la interfaz desde Windows, comprobó que el CSS se aplicaba correctamente y validó los botones de ambos perfiles.

## 6. Integración de Flask con MySQL — versión 2.0

La segunda versión sustituyó los mensajes definidos en Python por consultas reales a MySQL, manteniendo la interfaz existente. La base `servientrega_db` y la tabla `perfiles` se prepararon y verificaron previamente, según el documento 09.

### 6.1. Dependencias actualizadas

Contenido final de `requirements.txt`:

```text
Flask==3.1.1
gunicorn==23.0.0
PyMySQL==1.1.1
```

### 6.2. Variables de entorno

Se creó `.env` con los parámetros de conexión:

```dotenv
DB_HOST=servientrega-mysql-do9ws9
DB_PORT=3306
DB_NAME=servientrega_db
DB_USER=servientrega_app
DB_PASSWORD=<CONTRASENA_PRIVADA_NO_DOCUMENTADA>
```

**Nota:** la línea de contraseña es una representación documental, no un valor que deba copiarse literalmente. La contraseña real se introdujo de forma interactiva y no se incluye aquí.

El archivo recibió permisos restrictivos:

```bash
chmod 600 .env
```

Se agregaron `.env` y `*.bak` a `.dockerignore`, para evitar incorporar secretos y respaldos a la imagen. El contenedor de prueba recibió las variables mediante `--env-file .env`. Este método evita escribir la contraseña en el código fuente, aunque las variables de entorno del contenedor siguen siendo accesibles a administradores autorizados del motor Docker; para un entorno productivo se recomienda un gestor de secretos.

### 6.3. Lógica de consulta

La función `obtener_perfil(codigo)` abre una conexión PyMySQL con `charset="utf8mb4"`, tiempos de espera de cinco segundos y un cursor que devuelve diccionarios. Ejecuta una consulta parametrizada:

```sql
SELECT codigo, nombre, mensaje
FROM perfiles
WHERE codigo = %s
  AND activo = 1
LIMIT 1;
```

El parámetro `codigo` se transmite separado del texto SQL, evitando interpolar directamente valores recibidos desde la petición web. La conexión se cierra en un bloque `finally`.

La ruta `GET /` acepta los valores `administrador` y `operador`; ante un valor no reconocido, utiliza `operador` como perfil predeterminado. Los datos recuperados se pasan a `index.html` como `rol_actual` y `rol`.

Ante errores de conexión o configuración, la ruta devuelve HTTP **503** y un mensaje genérico, sin exponer contraseñas al visitante. Si el perfil no está disponible, devuelve **404**.

### 6.4. Rutas de verificación

| Ruta | Propósito | Respuesta validada |
|---|---|---|
| `/health` | Comprobar Flask/Gunicorn, sin consultar MySQL | HTTP 200, `{"service":"portal-servientrega","status":"ok"}` |
| `/health/db` | Abrir conexión autenticada y ejecutar `SELECT 1` | HTTP 200, `{"database":"connected","status":"ok"}` |
| `/?rol=administrador` | Consultar el perfil Administrador y renderizar HTML | HTTP 200 |
| `/?rol=operador` | Consultar el perfil Operador y renderizar HTML | HTTP 200 |

**Interpretación:** `/health/db` acredita conectividad, autenticación y ejecución de SQL. Las dos rutas de perfiles, al devolver HTTP 200 con el código de la versión 2.0, respaldan que la aplicación recuperó registros activos y generó las páginas.

## 7. Comunicación de red con MySQL

Inicialmente el portal 1.0 estaba conectado a la red Docker `bridge`, mientras que MySQL operaba en `dokploy-network`.

Se verificó que `dokploy-network` utiliza el controlador `overlay`, ámbito `swarm` y `Attachable: true`. Por ello se conectó el contenedor original a dicha red sin detenerlo:

```bash
sudo docker network connect dokploy-network portal-servientrega
```

Se confirmó que el contenedor disponía de ambas redes y que `/health` continuaba respondiendo HTTP 200.

Dentro del contenedor Flask se comprobaron dos condiciones:

- **DNS interno:** `servientrega-mysql-do9ws9` resolvió a `10.0.1.8` en el momento de la prueba.
- **Conectividad TCP:** la apertura de conexión a `servientrega-mysql-do9ws9:3306` fue satisfactoria.

La IP `10.0.1.8` es una observación del laboratorio, no un valor fijo que deba codificarse en Flask. Se utiliza el nombre del servicio Docker para la conexión.

La unión manual de una red a un contenedor independiente puede requerir repetirse si se elimina y recrea dicho contenedor. En la versión 2.0, la red se especificó directamente al crear el contenedor de prueba.

## 8. Construcción y ejecución de la versión 2.0

### 8.1. Respaldo y comprobaciones previas

Antes de modificar `app.py`, se creó `app.py.bak`. Se comprobó la sintaxis con `python3 -m py_compile app.py` y la presencia de las funciones `obtener_perfil`, `inicio`, `health` y `health_db` mediante el módulo `ast` de Python. Ambas verificaciones resultaron satisfactorias.

### 8.2. Construcción de imagen

```bash
cd /home/adminserv/portal-servientrega
sudo docker build --tag portal-servientrega:2.0 .
```

La construcción finalizó correctamente en aproximadamente **12,8 segundos**. Se verificaron ambas imágenes:

```text
portal-servientrega:2.0  f81323ddd8b3  126MB
portal-servientrega:1.0  3f70a6af18d2  126MB
```

Los identificadores y tamaños corresponden a la verificación realizada y pueden cambiar tras reconstruir las imágenes.

La instalación del controlador se comprobó con:

```bash
sudo docker run --rm \
  --entrypoint python \
  portal-servientrega:2.0 \
  -c "import pymysql; print('PyMySQL: INSTALADO CORRECTAMENTE')"
```

Resultado: `PyMySQL: INSTALADO CORRECTAMENTE`. Durante la construcción, el portal original continuó respondiendo HTTP 200.

### 8.3. Ejecución aislada para validación

La versión 2.0 se ejecutó como un contenedor adicional, sin sustituir la versión 1.0:

```bash
sudo docker run -d \
  --name portal-servientrega-test \
  --network dokploy-network \
  --env-file .env \
  --publish 192.168.10.10:5001:5000 \
  portal-servientrega:2.0
```

El puerto **5001** del servidor se redirige al puerto **5000** interno del contenedor. La base MySQL continúa accesible únicamente mediante la red privada Docker.

**Estado observado:** `portal-servientrega-test` en ejecución, con publicación `192.168.10.10:5001->5000/tcp`.

## 9. Validaciones funcionales realizadas

### 9.1. Comprobación HTTP desde Ubuntu

Se ejecutaron las siguientes pruebas:

```bash
curl -s -i http://192.168.10.10:5001/health
curl -s -i http://192.168.10.10:5001/health/db

curl -s -o /dev/null -w 'HTTP %{http_code}\n' \
  'http://192.168.10.10:5001/?rol=administrador'

curl -s -o /dev/null -w 'HTTP %{http_code}\n' \
  'http://192.168.10.10:5001/?rol=operador'
```

| Prueba | Resultado observado | Estado |
|---|---|---|
| Contenedor `portal-servientrega-test` | `Up`, puerto 5001 publicado | Correcto |
| `GET /health` | HTTP 200; servicio `portal-servientrega`, estado `ok` | Correcto |
| `GET /health/db` | HTTP 200; base `connected`, estado `ok` | Correcto |
| `GET /?rol=administrador` | HTTP 200 | Correcto |
| `GET /?rol=operador` | HTTP 200 | Correcto |

### 9.2. Validación visual desde Windows

El usuario confirmó que pudo abrir **`http://192.168.10.10:5001/` desde Windows** y comprobar que ambos botones muestran los mensajes esperados:

**Administrador:**

> Bienvenido al panel administrativo. Desde este perfil se supervisa la infraestructura tecnológica de la sede.

**Operador:**

> Bienvenido al área operativa. Desde este perfil se apoyan las actividades diarias de la sede.

La comprobación demuestra que la interfaz de la versión integrada se visualiza correctamente desde el cliente del laboratorio y que la aplicación obtiene los mensajes de la tabla `perfiles`.

## 10. Incidencias y soluciones

| Incidencia / consideración | Acción realizada | Resultado |
|---|---|---|
| Permiso denegado al usar Docker sin privilegios | Se utilizaron comandos `sudo docker` | Construcciones y pruebas exitosas |
| Portal y MySQL en redes distintas | Se verificó `dokploy-network` y su atributo `Attachable: true`; se conectó el contenedor | DNS y TCP 3306 correctos |
| Primera versión sin integración SQL | Se añadió PyMySQL y consulta parametrizada a `perfiles` | Rutas de perfiles y `/health/db` con HTTP 200 |
| Posible alteración del código durante pegado en terminal | Se verificó sintaxis y estructura AST de `app.py` | Cuatro funciones presentes; sintaxis correcta |
| Riesgo de exponer credenciales en código o imagen | Variables `.env`, permisos `600`, exclusión `.dockerignore` | Configuración local comprobada |
| Riesgo de interrumpir la versión funcional | Se construyó imagen `2.0` y contenedor paralelo en puerto 5001 | Versión 1.0 continuó disponible |

La corrección de caracteres acentuados en los mensajes de MySQL se encuentra documentada en `09-servicio-mysql.md`.

## 11. Seguridad y limitaciones

1. **Alcance de red:** el portal se publica en la IP Host-only del servidor (`192.168.10.10`), destinada al laboratorio. No se verificó publicación a Internet.
2. **Credenciales:** la contraseña de MySQL no está escrita en `app.py` ni en el documento. El archivo `.env` tiene permisos `600` y está excluido del contexto de construcción Docker.
3. **Consulta segura:** el parámetro de perfil se incorpora a SQL mediante marcadores de PyMySQL; no se construye SQL concatenando entrada del usuario.
4. **Privilegios de ejecución:** la imagen inicia Gunicorn con un usuario de aplicación no privilegiado (`appuser`).
5. **Roles demostrativos:** seleccionar `?rol=administrador` **no autentica ni autoriza** a una persona. Los botones solo modifican la información visible.
6. **HTTP, no HTTPS:** el portal está disponible mediante HTTP en los puertos 5000 y 5001. **No se instaló certificado TLS ni se validó HTTPS**.
7. **Dokploy:** la plataforma Dokploy y el servicio MySQL están operativos, pero **el portal Flask no fue registrado ni desplegado como aplicación administrada por Dokploy**. Su ejecución se realizó mediante Docker CLI.
8. **Carácter temporal:** el contenedor `portal-servientrega-test` no se creó con una política de reinicio explícita; su permanencia tras reiniciar el servidor no está garantizada.
9. **Entorno académico:** no se realizaron pruebas de carga, recuperación ante desastres, monitoreo productivo ni endurecimiento integral de seguridad.

Estas limitaciones deben indicarse en la sustentación y en la matriz final de cumplimiento, especialmente si HTTPS o el despliegue web desde Dokploy son requisitos obligatorios de la actividad.

## 12. Operación y mantenimiento

### 12.1. Verificar contenedores e imágenes

```bash
sudo docker ps \
  --filter 'name=portal-servientrega' \
  --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'

sudo docker images portal-servientrega
```

### 12.2. Verificar el servicio y la base de datos

```bash
curl -s -i http://192.168.10.10:5001/health
curl -s -i http://192.168.10.10:5001/health/db
```

Una respuesta HTTP 200 de `/health/db` confirma la disponibilidad de una conexión autenticada y una consulta SQL simple en ese instante; no equivale a una auditoría integral de la base de datos.

### 12.3. Revisar registros

```bash
sudo docker logs --tail 50 portal-servientrega-test
```

Evitar publicar registros que puedan contener información confidencial.

### 12.4. Reinicio y recuperación

```bash
sudo docker start portal-servientrega-test
sudo docker restart portal-servientrega-test
```

Estos comandos se incluyen como procedimientos operativos, **no como pruebas ejecutadas**. No eliminan datos MySQL. Antes de reconstruir o reemplazar el contenedor, conservar una copia de los archivos del proyecto y comprobar que `.env` permanece fuera de la imagen.

### 12.5. Actualización controlada

Tras modificar código o dependencias, reconstruir una nueva imagen versionada y validar primero `/health`, `/health/db` y las rutas de perfiles en un contenedor separado. Evitar reemplazar directamente una versión operativa sin una comprobación previa. La conexión MySQL requiere la red privada y las variables de entorno correctas.

## 13. Evidencias del proyecto

Ubicación prevista: `AdminTI/capturas/`.

| Nº | Archivo | Contenido | Estado |
|---|---|---|---|
| 28 | `28-portal-web-administrador.png` | Portal original, perfil Administrador desde Windows | Confirmada |
| 29 | `29-portal-web-operador.png` | Portal original, perfil Operador desde Windows | Confirmada |
| 30 | `30-mysql-validacion-consultas.png` | Autenticación y consultas SQL de MySQL | Referencia al documento 09 |
| 31 | `31-mysql-servicio-activo-dokploy.png` | Servicio MySQL activo en Dokploy | Referencia al documento 09 |
| 32 | `32-portal-flask-mysql-integracion.png` | Portal 2.0 desde Windows con conexión MySQL | **Captura propuesta; guardado no confirmado** |

La validación visual de la versión 2.0 **sí fue confirmada por el usuario**. No se debe afirmar que el archivo de captura 32 ya está guardado hasta comprobarlo.

## 14. Criterios de cierre

| Criterio | Estado |
|---|---|
| Portal Flask accesible desde Windows | Cumplido |
| Mensajes diferenciados de Administrador y Operador | Cumplido |
| Ejecución en Docker con Gunicorn | Cumplido |
| Integración real Flask–MySQL | Cumplido |
| Comprobación de salud web y base de datos | Cumplido |
| Despliegue del portal administrado desde Dokploy | No realizado |
| HTTPS / certificado TLS | No realizado |
| Evidencia gráfica de versión 2.0 guardada | Pendiente de confirmar |

**Conclusión:** el portal institucional simulado quedó implementado y validado funcionalmente mediante Docker, Flask, Gunicorn y MySQL. La aplicación integrada responde desde Windows, consulta perfiles almacenados en MySQL y dispone de comprobaciones HTTP de disponibilidad. El cierre corresponde al **alcance implementado**, no al cumplimiento de funcionalidades no realizadas como HTTPS o despliegue de la aplicación desde Dokploy.

---

**Documentos relacionados:** `02-docker-dokploy.md`, `09-servicio-mysql.md`, `analisis.md` y `diagrama.mmd`.
