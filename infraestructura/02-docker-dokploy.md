# Implementación de Docker Engine y Dokploy

**Cliente:** Servientrega S. A. — entorno de infraestructura de sede (laboratorio controlado)  
**Servidor:** `srv-servientrega`  
**Documento:** `02-docker-dokploy.md`  
**Ubicación en el repositorio:** `infraestructura/02-docker-dokploy.md`  
**Fecha de verificación:** 19 de noviembre de 2026  
**Estado de implementación:** Instalado y validado para administración local por HTTP

---

## 1. Resumen ejecutivo

Se implementó una plataforma de administración y despliegue de contenedores sobre Ubuntu Server 24.04.5 LTS, mediante el instalador oficial de Dokploy. El procedimiento incorporó Docker Engine, Docker Compose, Docker Swarm y los servicios necesarios para el funcionamiento de Dokploy, incluyendo su base de datos interna PostgreSQL y el proxy inverso Traefik.

El servidor quedó operativo como nodo administrador de Docker Swarm. Se verificó el acceso autenticado al panel de Dokploy desde el equipo Windows anfitrión, a través de la red privada Host-only de VirtualBox, y se obtuvo una respuesta HTTP `200` en la comprobación final del servicio.

**Alcance:** este documento describe la plataforma de contenedores y su panel de administración. No incluye todavía el despliegue del portal web de la sede ni de la base de datos MySQL de la aplicación, que corresponden a implementaciones independientes. PostgreSQL 16, citado en este documento, es un componente interno de Dokploy y no sustituye la base de datos MySQL prevista para el portal.

## 2. Objetivo

Disponer de una plataforma centralizada para gestionar despliegues y servicios contenerizados, manteniendo una configuración reproducible y verificable sobre la infraestructura virtual de la sede.

Los objetivos técnicos de esta implementación fueron:

- Instalar Docker Engine y comprobar su disponibilidad como servicio del sistema.
- Habilitar Docker Swarm en un nodo administrador.
- Instalar y poner en funcionamiento Dokploy con sus componentes dependientes.
- Comprobar el acceso al panel administrativo desde Windows mediante la interfaz Host-only.
- Verificar la estabilidad de los contenedores y la respuesta del servicio web.

## 3. Infraestructura de partida

La plataforma se instaló sobre una máquina virtual previamente implementada y validada.

| Parámetro | Configuración |
|---|---|
| Hipervisor | Oracle VirtualBox 7.2.22 |
| Nombre de la máquina virtual | `srv-servientrega` |
| Sistema operativo | Ubuntu Server 24.04.5 LTS |
| Arquitectura | `amd64` |
| Procesadores virtuales | 2 vCPU |
| Memoria asignada | 8192 MB |
| Disco virtual | 50 GB |
| Usuario de administración | `adminserv` |
| Interfaz Bridged | `enp0s3` — `192.168.80.46/24` durante la implementación, por DHCP |
| Interfaz Host-only | `enp0s8` — `192.168.10.10/24`, estática |
| Equipo anfitrión en Host-only | `192.168.10.1/24` |
| Puerta de enlace predeterminada | `192.168.80.1`, a través de `enp0s3` |
| Acceso remoto | SSH desde Windows a `adminserv@192.168.10.10` |

La dirección `192.168.80.46` es dinámica y puede variar; la dirección `192.168.10.10` se utiliza como referencia estable para la administración dentro del laboratorio.

### 3.1. Comprobaciones previas

Antes de instalar se comprobó lo siguiente:

- Docker no estaba instalado; no se detectaron paquetes previos de Docker, `containerd` o `runc` en la consulta realizada.
- Los puertos TCP `80`, `443` y `3000` no estaban ocupados por servicios en escucha.
- La ruta hacia Internet utilizaba `enp0s3`; la ruta hacia Windows `192.168.10.1` utilizaba `enp0s8`.
- El servidor disponía de aproximadamente **7,3 GiB de memoria disponible** y **40 GB libres** en la partición raíz durante la revisión previa.
- `systemctl --failed` no mostró unidades fallidas.
- La solicitud HTTPS a `https://dokploy.com` respondió con `HTTP/2 200`.
- UFW se encontraba inactivo y `net.ipv4.ip_forward` tenía el valor `0` antes de la instalación. No se atribuye a ese valor el estado posterior de la red Docker; la comprobación correspondió al entorno inicial.

Estas comprobaciones permitieron ejecutar el instalador en un servidor sin instalaciones de Docker preexistentes ni conflictos iniciales en los puertos requeridos.

## 4. Decisión de implementación

Se adoptó una **instalación integrada de Docker y Dokploy**. La inspección previa del instalador descargado mostró que este comprueba la existencia de Docker y, si no está instalado, intenta incorporarlo mediante el mecanismo de instalación de Docker (`get.docker.com`).

Por ello, no se ejecutó una instalación manual separada de Docker Engine. Este enfoque evitó duplicar procedimientos y permitió mantener la secuencia aplicada realmente en el servidor.

El instalador examinado contenía una referencia a Docker `28.5.0`, inicialización de Docker Swarm y creación de servicios mediante `docker service create`. También utilizaba una dirección anunciada para Swarm, importante en servidores con más de una interfaz de red.

## 5. Preparación e inspección del instalador

Se creó un directorio local para conservar el script y revisarlo antes de ejecutarlo.

```bash
mkdir -p ~/instaladores/dokploy

curl -fSL --retry 3 \
  https://dokploy.com/install.sh \
  -o ~/instaladores/dokploy/install.sh
```

Se verificaron la existencia del archivo, su sintaxis Bash y su huella SHA-256:

```bash
ls -lh ~/instaladores/dokploy/install.sh

bash -n ~/instaladores/dokploy/install.sh \
  && echo "Sintaxis Bash correcta"

sha256sum ~/instaladores/dokploy/install.sh
```

**Resultados observados:** archivo de aproximadamente 16 KB, sintaxis Bash válida y huella registrada:

```text
6e4eb75cc26599ec258cce41a2e4dd6730d84160c154ab340c0f091f91ae04e8
```

La huella documenta la copia revisada; **no equivale por sí sola a una verificación criptográfica de autenticidad**, porque no se comparó con una firma o suma publicada de manera independiente por el proveedor.

### 5.1. Revisión funcional del script

Se inspeccionaron los apartados relativos a instalación de Docker, selección de la dirección anunciada, inicialización de Swarm, creación de servicios y salida final del instalador. Entre los comandos de consulta utilizados estuvieron:

```bash
grep -nE 'DOCKER_VERSION|get.docker.com|docker swarm init|ADVERTISE_ADDR|docker service create' \
  ~/instaladores/dokploy/install.sh

sed -n '125,165p' ~/instaladores/dokploy/install.sh
```

Se confirmó que la dirección anunciada podía establecerse explícitamente mediante `ADVERTISE_ADDR`. Esta posibilidad fue necesaria porque el servidor dispone de una interfaz Bridged y otra Host-only.

## 6. Instalación integrada

Se ejecutó el instalador previamente descargado con privilegios administrativos, especificando la IP estática Host-only como dirección anunciada de Docker Swarm.

```bash
sudo ADVERTISE_ADDR=192.168.10.10 \
  bash ~/instaladores/dokploy/install.sh
```

> **Nota de reproducibilidad:** el comando anterior refleja el mecanismo de ejecución utilizado para la implementación documentada. Antes de reutilizarlo en otra máquina, debe revisarse la versión vigente del instalador y adaptarse `ADVERTISE_ADDR` a la interfaz correcta del nuevo servidor. No se recomienda ejecutar automáticamente una copia de script distinta sin inspeccionarla.

### 6.1. Operaciones observadas

Durante la instalación se registraron las siguientes operaciones:

1. Instalación de Docker Engine `28.5.0`.
2. Aplicación de retenciones (`apt-mark hold`) a los paquetes `docker-ce`, `docker-ce-cli` y `docker-ce-rootless-extras`, según la salida del instalador. Estas retenciones deberán considerarse al planificar actualizaciones futuras.
3. Inicialización de Docker Swarm con la dirección anunciada `192.168.10.10`.
4. Creación de la red requerida por Dokploy.
5. Generación de credenciales internas y secretos de Docker para la plataforma.
6. Creación de PostgreSQL 16 como servicio de soporte de Dokploy.
7. Creación del servicio principal de Dokploy.
8. Descarga y puesta en marcha de Traefik `v3.7.19`.

El instalador concluyó con el mensaje:

```text
Congratulations, Dokploy is installed!
```

También indicó el acceso administrativo mediante `http://192.168.10.10:3000` y, como alternativa en la red Bridged durante esa sesión, `http://192.168.80.46:3000`.

**Confidencialidad:** durante la inicialización de Swarm se generó un token de incorporación de nodos. Los tokens, contraseñas y secretos no deben incorporarse al documento ni a las capturas compartidas. Debido a que el token de incorporación apareció en una captura de diagnóstico, se recomienda rotarlo antes de incorporar otros nodos al clúster.

## 7. Arquitectura resultante

La instalación quedó organizada de la siguiente manera:

```text
Equipo Windows anfitrión
192.168.10.1
        |
        | Red privada Host-only de VirtualBox
        v
Ubuntu Server 24.04.5 LTS — srv-servientrega
192.168.10.10 (enp0s8)
        |
        +-- Docker Engine 28.5.0
        |     +-- Docker Compose v5.8.0
        |     +-- Docker Swarm (nodo manager / leader)
        |           +-- Dokploy v0.31.4      [TCP 3000]
        |           +-- PostgreSQL 16        [servicio interno]
        |           +-- Traefik v3.7.19      [TCP 80/443]
        |
        +-- enp0s3: red Bridged / acceso a Internet
```

La dirección `192.168.10.10` se estableció como dirección anunciada de Swarm. El panel administrativo de Dokploy utiliza HTTP en el puerto `3000` dentro del laboratorio.

### 7.1. Puertos observados

| Puerto | Protocolo | Uso | Observación |
|---|---|---|---|
| 3000 | TCP | Panel administrativo de Dokploy | Publicado en modo `host` |
| 80 | TCP | Entrada HTTP de Traefik | Puerto publicado por Docker |
| 443 | TCP | Entrada HTTPS de Traefik | Puerto publicado por Docker; esto no implica que el panel de Dokploy ya utilice HTTPS |
| 443 | UDP | Tráfico asociado a Traefik | Publicación observada en el contenedor |
| 2377, 7946, 4789 | Puertos asociados a Swarm | Comunicaciones de clúster | Se verificó inicialmente que no estaban ocupados; no se configuró un clúster multinodo |

La publicación del puerto 3000 se verificó mediante:

```bash
sudo docker service inspect dokploy \
  --format '{{json .Endpoint.Spec.Ports}}'
```

Resultado:

```json
[{"Protocol":"tcp","TargetPort":3000,"PublishedPort":3000,"PublishMode":"host"}]
```

La consulta de reglas NAT también mostró una redirección gestionada por Docker hacia la IP interna del contenedor. Esa dirección interna es dinámica y no debe emplearse como punto de acceso administrativo estable.

### 7.2. Consideraciones de seguridad del laboratorio

Se acordó utilizar HTTP para la administración local durante esta implementación. **HTTP no cifra las credenciales ni el tráfico**, y la publicación del puerto 3000 no está restringida exclusivamente a la interfaz Host-only: también puede ser alcanzable desde la red Bridged si la conectividad de esa red lo permite.

Por ello, el uso documentado queda limitado a un laboratorio controlado, con contraseña exclusiva y sin exposición deliberada a Internet. No se configuraron reglas adicionales de UFW o `iptables` ni certificados HTTPS para el panel en esta implementación. Antes de llevar la plataforma a un entorno productivo deberán evaluarse HTTPS, restricciones de acceso, gestión de secretos, respaldos y actualización de imágenes.

## 8. Configuración de la cuenta administrativa

Desde el navegador del equipo Windows anfitrión se accedió a:

```text
http://192.168.10.10:3000/register
```

La interfaz mostró el formulario inicial **Setup the server**, desde el cual se creó la cuenta administrativa. Por motivos de seguridad no se registran en este documento el correo ni la contraseña utilizados.

Tras completar el registro, se verificó el acceso autenticado a:

```text
http://192.168.10.10:3000/dashboard/home
```

La interfaz presentó la pantalla de bienvenida de Dokploy, confirmando el funcionamiento del panel y la sesión administrativa desde Windows. No se creó todavía ningún proyecto ni se desplegó una aplicación.

## 9. Validaciones técnicas

### 9.1. Versiones y estado del servicio

Comandos utilizados:

```bash
sudo docker --version
sudo docker compose version
systemctl is-active docker
```

Resultados finales:

```text
Docker version 28.5.0, build 887030f
Docker Compose version v5.8.0
active
```

### 9.2. Estado del nodo Swarm

Comando:

```bash
sudo docker node ls
```

Resultado verificado:

| Nodo | Estado | Disponibilidad | Rol |
|---|---|---|---|
| `srv-servientrega` | `Ready` | `Active` | `Leader` |

Se comprobó que el nodo ejecutaba Docker Engine `28.5.0`.

### 9.3. Réplicas de los servicios

Comando:

```bash
sudo docker service ls
```

Resultado final:

| Servicio | Imagen | Réplicas |
|---|---|---|
| `dokploy` | `dokploy/dokploy:v0.31.4` | `1/1` |
| `dokploy-postgres` | `postgres:16` | `1/1` |

Traefik se observó en ejecución como contenedor `dokploy-traefik`, con imagen `traefik:v3.7.19`.

### 9.4. Estado de contenedores

Comando:

```bash
sudo docker ps --format 'table {{.Names}}\t{{.Status}}'
```

En la verificación final se observaron:

- Contenedor de Dokploy en ejecución durante aproximadamente tres minutos, con estado **`healthy`**.
- Contenedor de PostgreSQL en ejecución.
- Contenedor de Traefik en ejecución.

Los identificadores completos y nombres de tareas pueden cambiar cuando Docker Swarm reemplaza contenedores; por ello, para el seguimiento se priorizan los nombres de servicio y el estado de sus réplicas.

### 9.5. Respuesta HTTP del panel

Comando:

```bash
curl -sS -o /dev/null \
  -w 'HTTP: %{http_code}\n' \
  --max-time 10 \
  http://127.0.0.1:3000
```

Resultado final:

```text
HTTP: 200
```

En una comprobación anterior se obtuvo `HTTP: 307`, correspondiente a una redirección de la aplicación. La verificación final, posterior a la creación de la cuenta administrativa, devolvió `200`.

### 9.6. Acceso desde el equipo anfitrión

Se abrió el panel en un navegador Windows mediante `http://192.168.10.10:3000`. Se verificaron tanto la página de registro inicial como, posteriormente, el panel autenticado en `/dashboard/home`.

**Resultado:** acceso funcional desde la red Host-only y administración inicial completada.

## 10. Incidencia observada durante la inicialización

### 10.1. Síntomas

En las primeras comprobaciones posteriores a la instalación, el servicio `dokploy` mostró temporalmente `0/1` réplicas. El historial de tareas registró reemplazos sucesivos, mientras que PostgreSQL permanecía en `1/1`.

Los registros de Dokploy mostraban, entre otros, los mensajes:

```text
Postgres is reachable
Migration complete
Initialization complete
Server Started on: http://0.0.0.0:3000
```

Se observó asimismo un error de programación de una tarea:

```text
no suitable node (host-mode port already in use on 1 node)
```

Este mensaje identifica un conflicto temporal al intentar programar una tarea que requería el puerto 3000, ocupado por otra tarea en el único nodo disponible. **No demuestra por sí solo la causa original de todos los reemplazos.**

### 10.2. Diagnóstico

Se consultaron las tareas de Swarm, el estado de contenedores, sus verificaciones de salud y los recursos del servidor.

Se constató que:

- Un contenedor de Dokploy llegó a estar `running` y `healthy`.
- Los contenedores anteriores mostraban terminaciones con código `0`.
- La comprobación de OOM indicó `false` para el contenedor inspeccionado.
- La memoria disponible era aproximadamente **6,7 GiB** durante el diagnóstico.
- La política de actualización consultada indicaba `stop-first`.
- La política de reinicio consultada indicaba `any`, con demora de cinco segundos.

### 10.3. Resultado

Sin reinstalar Docker ni Dokploy y sin eliminar contenedores o volúmenes, el servicio alcanzó posteriormente `1/1` réplicas. Las verificaciones siguientes confirmaron un contenedor saludable, respuesta HTTP y acceso administrativo desde Windows.

**Conclusión técnica:** incidencia transitoria observada durante la estabilización inicial, resuelta en el estado final comprobado. La causa primaria de los reemplazos no quedó demostrada de forma concluyente; si el comportamiento reaparece, deberán revisarse nuevamente las tareas, los eventos del daemon y los registros de salud.

## 11. Comandos de operación y mantenimiento

Los siguientes comandos permiten consultar el estado de la plataforma sin modificar su configuración:

```bash
# Estado del motor Docker
systemctl is-active docker

# Versiones instaladas
docker --version
docker compose version

# Estado del nodo Swarm
sudo docker node ls

# Servicios y réplicas
sudo docker service ls

# Contenedores activos
sudo docker ps

# Tareas del servicio Dokploy
sudo docker service ps dokploy

# Últimos registros del servicio
sudo docker service logs dokploy --tail 50

# Comprobación HTTP local
curl -sS -o /dev/null -w 'HTTP: %{http_code}\n' http://127.0.0.1:3000
```

Para la administración web desde el anfitrión Windows:

```text
http://192.168.10.10:3000
```

No se incluyen comandos de actualización o reinstalación automática, ya que deben planificarse teniendo en cuenta las versiones instaladas, las retenciones de paquetes y la conservación de datos persistentes.

## 12. Evidencias

Las evidencias se almacenan en la carpeta general `capturas/`, sin crear una carpeta adicional de documentación. Los nombres siguientes son **convenciones recomendadas** y deben ajustarse a los nombres reales de los archivos guardados:

| Nombre sugerido | Contenido |
|---|---|
| `08-prerrequisitos-docker-dokploy.png` | Comprobación de paquetes, recursos y conectividad |
| `09-instalacion-docker-dokploy.png` | Instalador finalizado y Swarm inicializado; ocultar cualquier token |
| `10-docker-swarm-servicios.png` | Versiones, nodo Swarm y servicios desplegados |
| `11-acceso-dokploy.png` | Panel administrativo accesible desde Windows, sin credenciales visibles |
| `12-validacion-final-docker-dokploy.png` | Docker, Compose, Swarm, réplicas, contenedores y HTTP `200` |

Las capturas de diagnóstico de la incidencia pueden conservarse como soporte complementario, siempre que se oculten tokens o secretos.

## 13. Resultados y alcance de la entrega

Al concluir la implementación se verificó:

1. Docker Engine `28.5.0` instalado y activo.
2. Docker Compose `v5.8.0` disponible.
3. Docker Swarm operativo con `srv-servientrega` como nodo `Ready`, `Active` y `Leader`.
4. Dokploy `v0.31.4` y PostgreSQL 16 con `1/1` réplicas.
5. Traefik `v3.7.19` en ejecución.
6. Contenedor principal de Dokploy con estado `healthy`.
7. Respuesta local `HTTP 200` del panel.
8. Acceso autenticado desde Windows a través de `192.168.10.10:3000`.

La plataforma queda preparada para la posterior incorporación de proyectos, aplicaciones y bases de datos contenerizadas. **No se declara todavía validado el despliegue de aplicaciones**, porque no formó parte de las pruebas realizadas en esta implementación.

## 14. Recomendaciones operativas

- Mantener la dirección estática Host-only `192.168.10.10` para la administración desde el equipo anfitrión.
- Utilizar credenciales exclusivas del laboratorio y no almacenarlas en capturas o archivos del repositorio.
- Rotar el token de incorporación de Swarm que apareció en una captura antes de admitir nuevos nodos.
- Revisar las retenciones de paquetes Docker al planificar actualizaciones.
- Comprobar periódicamente las réplicas, el estado de salud y los registros de los servicios.
- Evaluar HTTPS, control de acceso a puertos y respaldos antes de cualquier uso fuera del laboratorio controlado.
- Documentar por separado el despliegue del portal web y la base de datos MySQL de la solución.

---

**Resultado final:** Docker Engine y Dokploy quedaron instalados y validados para administración local en el servidor virtual `srv-servientrega`, con acceso funcional desde Windows y servicios principales operativos.
