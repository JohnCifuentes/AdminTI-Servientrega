# SERVIENTREGA S.A.
## Implementación y validación del servicio DNS interno con dnsmasq

**Documento técnico:** 03-servicio-dns-dnsmasq  
**Infraestructura:** Sede simulada de Servientrega S.A.  
**Servidor:** `srv-servientrega`  
**Sistema operativo:** Ubuntu Server 24.04.5 LTS  
**Servicio:** DNS interno y reenvío de consultas externas  
**Dominio interno:** `servientrega.lab`  
**Fecha de verificación:** 19 de noviembre de 2026

---

## 1. Resumen ejecutivo

Se implementó un servicio de resolución de nombres DNS para la red interna de Servientrega S.A., utilizando **dnsmasq** sobre Ubuntu Server. El servicio permite asociar nombres internos con la dirección del servidor de infraestructura y reenviar consultas de dominios públicos a un servidor DNS ascendente.

La implementación fue comprobada mediante consultas directas desde Ubuntu y Windows, pruebas de conectividad al puerto DNS y una solicitud HTTP al panel Dokploy utilizando el nombre de host interno con resolución explícita de la dirección de destino.

El servicio DNS opera sobre la interfaz de laboratorio **Host-only**, sin sustituir el mecanismo de resolución DNS que utiliza Ubuntu para sus propias consultas generales ni modificar automáticamente la configuración DNS del equipo Windows anfitrión.

## 2. Objetivo y alcance

Proporcionar resolución de nombres para los servicios alojados en la infraestructura interna y permitir que los clientes de la red consulten nombres públicos a través del mismo servidor DNS.

El alcance implementado comprende:

- Instalación de dnsmasq y verificación del servicio administrado por systemd.
- Escucha DNS en la dirección `192.168.10.10`, puerto 53 TCP y UDP.
- Configuración del dominio local `servientrega.lab` y sus registros de tipo A.
- Reenvío de consultas externas al DNS ascendente `192.168.80.1`.
- Pruebas funcionales desde el servidor Ubuntu y desde el anfitrión Windows.
- Diagnóstico y corrección de incidencias de configuración y arranque.

No forma parte de esta implementación la distribución automática de parámetros DNS mediante DHCP, ni la configuración de todos los equipos cliente para utilizar el DNS interno como servidor predeterminado.

## 3. Arquitectura y direccionamiento

| Elemento | Valor | Función |
|---|---|---|
| Servidor | `srv-servientrega` | Host de infraestructura |
| Sistema operativo | Ubuntu Server 24.04.5 LTS | Plataforma de ejecución |
| Interfaz `enp0s8` | `192.168.10.10/24` | Red Host-only y escucha del DNS interno |
| Interfaz `enp0s3` | `192.168.80.46/24` durante las pruebas | Conectividad hacia la red principal mediante DHCP |
| Anfitrión Windows | `192.168.10.1/24` | Cliente de pruebas en la red Host-only |
| DNS ascendente | `192.168.80.1` | Resolución de nombres públicos |
| Dominio DNS interno | `servientrega.lab` | Espacio de nombres del laboratorio |
| Servicio DNS | Puerto 53, TCP y UDP | Consultas de resolución de nombres |
| Panel Dokploy | Puerto HTTP 3000 | Servicio web utilizado para comprobar conectividad |

La dirección `192.168.80.46` corresponde a una asignación DHCP observada durante la implementación y podría variar. La dirección `192.168.10.10` es la referencia estable del servicio DNS interno.

**Flujo de consultas:** el cliente Windows (`192.168.10.1`) consulta dnsmasq (`192.168.10.10:53`). Los nombres de `servientrega.lab` se responden localmente; las consultas públicas se remiten a `192.168.80.1`, según la configuración de reenvío.

La instalación existente de `systemd-resolved` conserva su escucha local en `127.0.0.53` y `127.0.0.54`. dnsmasq utiliza la dirección `192.168.10.10`, por lo que ambos componentes pueden coexistir sin disputar el mismo socket.

## 4. Componentes y archivos de configuración

| Componente | Ubicación o comando | Propósito |
|---|---|---|
| dnsmasq | `dnsmasq --version` | Servicio DNS ligero |
| Configuración interna | `/etc/dnsmasq.d/servientrega.conf` | Dirección de escucha y registros internos |
| Reenvío externo | `/etc/dnsmasq.d/reenviadores.conf` | Servidor DNS ascendente |
| Respaldos | `/etc/dnsmasq-respaldos/` | Conservación de versiones anteriores de configuración |
| Gestión del servicio | `systemctl` | Arranque y estado operativo |
| Diagnóstico DNS | `dig` | Consultas y comprobación de respuestas |
| Resolución del sistema | `systemd-resolved` | Resolución local de Ubuntu, independiente del servicio expuesto a clientes |

### 4.1. Configuración DNS interna

El archivo `/etc/dnsmasq.d/servientrega.conf` contiene las siguientes directivas funcionales, verificadas durante las pruebas:

```ini
# Escuchar exclusivamente en la dirección Host-only
listen-address=192.168.10.10
bind-interfaces

# Funcionalidad DNS; puerto 53
port=53

# No incorporar automáticamente entradas de /etc/hosts
no-hosts

# Registrar consultas para diagnóstico
log-queries

# Dominio interno
 domain=servientrega.lab
local=/servientrega.lab/

# Registros A internos
host-record=servientrega.lab,192.168.10.10
host-record=srv-servientrega.servientrega.lab,192.168.10.10
host-record=dokploy.servientrega.lab,192.168.10.10
host-record=www.servientrega.lab,192.168.10.10
```

> **Nota de reproducción:** la sangría anterior a `domain=` es únicamente de presentación; puede eliminarse al copiar el ejemplo. El listado describe las directivas funcionales verificadas, no pretende ser una transcripción literal de todos los comentarios del archivo instalado.

La directiva `local=/servientrega.lab/` evita remitir a DNS externos las consultas de ese dominio interno.

### 4.2. Configuración de reenvío externo

El archivo `/etc/dnsmasq.d/reenviadores.conf` fue creado con el contenido:

```ini
# SERVIENTREGA - REENVÍO DNS EXTERNO

# Evitar leer servidores DNS del sistema
no-resolv

# Servidor DNS ascendente de la red principal
server=192.168.80.1
```

`no-resolv` evita depender de los servidores listados por el resolvedor local, y `server=` determina el destino de las consultas externas. Esta separación permite administrar el DNS interno y el reenvío en archivos independientes.

## 5. Procedimiento de implementación

### 5.1. Inspección inicial

Antes de instalar dnsmasq se revisaron las interfaces, el puerto 53, el estado de `systemd-resolved` y la existencia previa del paquete:

```bash
hostname
ip -br addr
sudo ss -lntup | grep ':53'
resolvectl status
systemctl is-active systemd-resolved
command -v dnsmasq || echo 'dnsmasq no instalado'
```

Se identificó que `systemd-resolved` utilizaba las direcciones locales `127.0.0.53` y `127.0.0.54` para el puerto DNS.

### 5.2. Instalación de dnsmasq

Se instaló el paquete desde los repositorios de Ubuntu:

```bash
sudo apt update
sudo apt install dnsmasq

dnsmasq --version
```

La versión observada fue **dnsmasq 2.91**. En el primer intento de arranque automático se registró una incidencia por ocupación del puerto 53; su tratamiento se documenta en la sección 7.

### 5.3. Configuración del servicio interno

Se creó el archivo `/etc/dnsmasq.d/servientrega.conf` con las directivas de escucha, dominio y registros descritas en la sección 4.1.

Se mantuvo `systemd-resolved` activo, asignando a dnsmasq únicamente la IP Host-only `192.168.10.10`. La configuración se verificó mediante:

```bash
sudo dnsmasq --test
sudo systemctl restart dnsmasq
systemctl is-active dnsmasq
sudo ss -lntup | grep ':53'
```

La validación final mostró **`dnsmasq: syntax check OK.`**, el servicio en estado **`active`** y escucha TCP/UDP en `192.168.10.10:53`.

### 5.4. Configuración del reenvío DNS

Inicialmente, las consultas a nombres internos funcionaban, pero las consultas públicas dirigidas a dnsmasq devolvían `REFUSED`. Para habilitar el reenvío se creó `/etc/dnsmasq.d/reenviadores.conf` con las directivas de la sección 4.2.

Se comprobó que el DNS del router `192.168.80.1` respondía consultas públicas antes de incorporarlo como ascendente.

La sintaxis de los archivos se validó con:

```bash
sudo dnsmasq --test
sudo cat /etc/dnsmasq.d/reenviadores.conf
sudo systemctl restart dnsmasq
systemctl is-active dnsmasq
```

Tras el reinicio, las consultas externas a través de `192.168.10.10` comenzaron a devolver respuestas DNS válidas.

## 6. Registros DNS implementados

| Nombre | Tipo | Dirección IPv4 | Uso previsto |
|---|---|---|---|
| `servientrega.lab` | A | `192.168.10.10` | Dominio principal |
| `srv-servientrega.servientrega.lab` | A | `192.168.10.10` | Identificación del servidor |
| `dokploy.servientrega.lab` | A | `192.168.10.10` | Panel de administración Dokploy |
| `www.servientrega.lab` | A | `192.168.10.10` | Nombre reservado para el portal web interno |

El registro `www.servientrega.lab` identifica el destino DNS previsto; **no demuestra por sí mismo que el portal web ya esté desplegado**.

## 7. Incidencias identificadas y resolución

### 7.1. Conflicto inicial del puerto 53

**Síntoma:** dnsmasq no pudo iniciar y registró el mensaje:

```text
failed to create listening socket for port 53: Address already in use
```

**Análisis:** `systemd-resolved` ya estaba activo en el puerto 53 de las direcciones loopback. Se ajustó la configuración de dnsmasq para restringir su escucha a `192.168.10.10` mediante `listen-address` y `bind-interfaces`, evitando deshabilitar la resolución local de Ubuntu.

**Resultado:** se comprobó la coexistencia de `systemd-resolved` en loopback y dnsmasq en la IP Host-only.

### 7.2. Fallo de reinicio pese a sintaxis válida

**Síntoma:** `dnsmasq --test` devolvía `syntax check OK`, pero el servicio llegó a fallar en la comprobación previa al arranque (`ExecStartPre`).

**Análisis y corrección:** se detectó un archivo de respaldo con extensión `.bak` dentro de `/etc/dnsmasq.d/`. Para evitar que copias de configuración interfirieran con las comprobaciones del servicio, se creó un directorio de respaldos separado y se trasladó el archivo allí:

```bash
sudo mkdir -p /etc/dnsmasq-respaldos
sudo mv /etc/dnsmasq.d/servientrega.conf.bak /etc/dnsmasq-respaldos/
sudo dnsmasq --test
sudo systemctl restart dnsmasq
```

**Resultado:** dnsmasq volvió al estado `active` y se verificó su escucha en el puerto 53. La evidencia muestra la recuperación tras retirar el respaldo del directorio de configuración; no se dispone de un diagnóstico adicional que aísle de forma definitiva el comportamiento interno de `ExecStartPre`.

### 7.3. Rechazo de consultas a dominios públicos

**Síntoma:** las consultas directas a `google.com` mediante `@192.168.10.10` respondían con `REFUSED`, mientras que el DNS del router `192.168.80.1` respondía correctamente.

**Corrección:** se configuró explícitamente el reenvío mediante `no-resolv` y `server=192.168.80.1`, se validó la sintaxis y se reinició dnsmasq.

**Resultado:** se obtuvieron respuestas válidas para `google.com`, `ubuntu.com` y `dokploy.com` desde Ubuntu, así como para `google.com` desde Windows.

## 8. Validaciones técnicas y resultados

### 8.1. Servicio y puertos

```bash
systemctl is-active dnsmasq
sudo ss -lntup | grep '192.168.10.10:53'
```

**Resultado observado:** `active`; sockets DNS TCP y UDP escuchando en `192.168.10.10:53`.

### 8.2. Consultas de registros internos desde Ubuntu

```bash
dig @192.168.10.10 servientrega.lab A +short
dig @192.168.10.10 srv-servientrega.servientrega.lab A +short
dig @192.168.10.10 dokploy.servientrega.lab A +short
dig @192.168.10.10 www.servientrega.lab A +short
```

**Resultado observado:** las cuatro consultas devolvieron `192.168.10.10`.

También se verificó que una consulta a un nombre inexistente del dominio interno devolvía `NXDOMAIN`.

### 8.3. Consultas públicas desde Ubuntu

```bash
dig @192.168.10.10 google.com A +time=3 +tries=1
dig @192.168.10.10 ubuntu.com A +time=3 +tries=1
dig @192.168.10.10 dokploy.com A +time=3 +tries=1
```

**Resultado observado:** respuestas `NOERROR` con direcciones IPv4 públicas. Estas direcciones pueden cambiar entre consultas por la naturaleza de los servicios externos.

### 8.4. Conectividad y resolución desde Windows

Se utilizaron comandos de Windows PowerShell para consultar explícitamente el servidor DNS interno:

```powershell
Test-NetConnection 192.168.10.10 -Port 53

Resolve-DnsName servientrega.lab -Server 192.168.10.10 -Type A
Resolve-DnsName srv-servientrega.servientrega.lab -Server 192.168.10.10 -Type A
Resolve-DnsName dokploy.servientrega.lab -Server 192.168.10.10 -Type A
Resolve-DnsName www.servientrega.lab -Server 192.168.10.10 -Type A
Resolve-DnsName google.com -Server 192.168.10.10 -Type A
```

**Resultados observados:**

- `TcpTestSucceeded: True` para el puerto 53 TCP.
- Los cuatro nombres internos devolvieron `192.168.10.10`.
- La consulta externa a `google.com` devolvió una dirección IPv4 pública (`172.217.162.142` en la evidencia final).

La prueba `Test-NetConnection` valida el puerto TCP; las respuestas DNS observadas mediante `Resolve-DnsName` verifican adicionalmente la operación del servicio de resolución, sin constituir por sí solas una medición exhaustiva de ambos transportes DNS.

### 8.5. Respuesta HTTP de Dokploy utilizando el nombre interno

Desde Windows se ejecutó:

```powershell
curl.exe -I --resolve dokploy.servientrega.lab:3000:192.168.10.10 http://dokploy.servientrega.lab:3000/
```

**Resultado observado:** `HTTP/1.1 200 OK` y encabezados HTTP del panel Dokploy.

La opción `--resolve` asocia explícitamente el nombre con la IP durante esta solicitud. Por tanto, esta prueba confirma la accesibilidad HTTP y la aceptación del nombre de host, **pero no constituye una prueba de que Windows o Chrome hayan adoptado dnsmasq como resolvedor predeterminado**.

## 9. Consideraciones operativas

- El servicio DNS interno está vinculado a `192.168.10.10`, la interfaz Host-only del laboratorio.
- El DNS ascendente `192.168.80.1` depende de la disponibilidad de la red principal y puede requerir actualización si cambia el entorno de conexión.
- La resolución de `servientrega.lab` en un cliente requiere consultar `192.168.10.10` explícitamente o configurar ese servidor como DNS del cliente.
- El acceso a Dokploy se comprobó mediante **HTTP**, conforme al alcance operativo del laboratorio; no se afirma que exista protección HTTPS para este nombre interno.
- Los registros DNS internos pueden existir antes del despliegue efectivo de los servicios asociados.
- No se alteró el DNS predeterminado de Windows durante estas verificaciones.

## 10. Operación y mantenimiento

Comandos de comprobación y diagnóstico:

```bash
# Verificar sintaxis antes de aplicar cambios
sudo dnsmasq --test

# Consultar estado
sudo systemctl status dnsmasq --no-pager -l

# Reiniciar después de cambios validados
sudo systemctl restart dnsmasq

# Comprobar escucha DNS
sudo ss -lntup | grep ':53'

# Consultar errores recientes
sudo journalctl -u dnsmasq -n 30 --no-pager

# Validar registros internos y resolución pública
dig @192.168.10.10 servientrega.lab A +short
dig @192.168.10.10 google.com A +short
```

Se recomienda mantener los respaldos de configuración **fuera** de `/etc/dnsmasq.d/`, documentar cualquier modificación de los registros y repetir las pruebas desde Ubuntu y Windows después de cambios de red.

## 11. Evidencias de implementación

Las siguientes evidencias corresponden a las capturas obtenidas durante la ejecución y verificación del servicio. **Los nombres sugeridos permiten organizar los archivos; no implican que ya existan con esos nombres en el repositorio.**

| Identificador sugerido | Evidencia | Contenido que debe mostrar |
|---|---|---|
| DNS-01 | `01-diagnostico-inicial-dns.png` | Interfaces, puerto 53 y estado inicial de `systemd-resolved` |
| DNS-02 | `02-instalacion-dnsmasq.png` | Instalación, versión 2.91 e incidencia inicial |
| DNS-03 | `03-configuracion-dns-interno.png` | Directivas de `servientrega.conf` y registros A |
| DNS-04 | `04-servicio-dns-activo.png` | `dnsmasq` activo y escucha TCP/UDP en `192.168.10.10:53` |
| DNS-05 | `05-validacion-dns-interno.png` | Consultas `dig` de los cuatro nombres internos |
| DNS-06 | `06-reenvio-dns-externo.png` | Contenido de `reenviadores.conf` y validación de sintaxis |
| DNS-07 | `07-validacion-dns-externo.png` | Consultas `dig` a dominios públicos con respuestas `NOERROR` |
| DNS-08 | `08-validacion-dns-windows.png` | Consultas desde PowerShell al DNS `192.168.10.10` |
| DNS-09 | `09-acceso-http-dokploy.png` | Solicitud `curl.exe --resolve` con respuesta `HTTP/1.1 200 OK` |

Se sugiere conservar estas capturas en una carpeta de evidencias asociada a este documento y ajustar los nombres de la tabla a los archivos efectivamente guardados.

## 12. Conclusión técnica

La implementación de **dnsmasq** en `srv-servientrega` quedó operativa para la red Host-only `192.168.10.0/24`. Las pruebas realizadas demuestran que el servidor responde a los registros internos de `servientrega.lab`, resuelve nombres públicos mediante reenvío DNS y atiende consultas directas desde el anfitrión Windows.

La resolución interna y externa fue validada con herramientas DNS y se comprobó adicionalmente que el panel Dokploy responde por HTTP cuando se utiliza el nombre interno con una asociación de IP explícita.

La integración automática de los clientes con el DNS interno podrá abordarse cuando se configure la resolución predeterminada de cada equipo, sin que ello afecte los resultados ya comprobados del servicio.
