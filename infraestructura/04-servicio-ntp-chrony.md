# SERVIENTREGA S.A.
## Documento técnico de implementación — Servicio NTP con Chrony

**Código:** INF-SRV-04  
**Servicio:** Sincronización horaria de red (NTP)  
**Servidor:** `srv-servientrega`  
**Sistema operativo:** Ubuntu Server 24.04.5 LTS  
**Dirección del servicio:** `192.168.10.10`  
**Red de clientes autorizada:** `192.168.10.0/24`  
**Estado de implementación:** Configurado y funcional; estabilidad verificada durante las comprobaciones recientes  
**Fecha de documentación:** 19 de noviembre de 2026

---

## 1. Resumen ejecutivo

Se implementó un servicio de sincronización horaria mediante **Chrony** en el servidor `srv-servientrega`, con el objetivo de proporcionar una referencia de tiempo común a los equipos conectados a la red interna de Servientrega S.A.

El servidor consulta fuentes NTP externas a través de su interfaz de salida a Internet y ofrece el servicio NTP a los clientes autorizados de la red privada `192.168.10.0/24`, escuchando en la dirección `192.168.10.10`, puerto **UDP 123**.

Se verificaron la ejecución del servicio, la conectividad con fuentes externas, la autorización de clientes, la respuesta desde un equipo Windows y la recuperación de la sincronización del reloj del sistema. Durante las pruebas se identificaron saltos temporales asociados al entorno virtualizado; posteriormente, la sincronización volvió a establecerse y no se observaron nuevos saltos ni pérdidas de sincronización en la consulta final de eventos recientes.

El servicio queda disponible para su utilización en la infraestructura interna. Se recomienda supervisar su estabilidad después de reinicios o cambios en la configuración del equipo anfitrión.

## 2. Objetivo y alcance

### 2.1 Objetivo

Centralizar la referencia horaria de los sistemas de la red interna para favorecer la consistencia de registros de eventos, auditorías, autenticación y operación coordinada de los servicios de infraestructura.

### 2.2 Alcance

- Instalación y configuración de Chrony en Ubuntu Server.
- Consulta de servidores NTP públicos como referencias de tiempo.
- Publicación del servicio NTP en la interfaz de red privada del servidor.
- Autorización de consultas de clientes del segmento `192.168.10.0/24`.
- Verificación del servicio desde Ubuntu y Windows.
- Diagnóstico y seguimiento de eventos de sincronización durante la puesta en funcionamiento.

**Fuera del alcance:** la configuración automática de todos los equipos clientes y la garantía de precisión horaria permanente ante fallas del hipervisor o de la conectividad externa.

## 3. Arquitectura de la solución

| Elemento | Configuración |
|---|---|
| Nombre del servidor | `srv-servientrega` |
| Plataforma | Máquina virtual Ubuntu Server sobre Oracle VirtualBox |
| Servicio de tiempo | Chrony (`chronyd`) |
| Dirección NTP interna | `192.168.10.10` |
| Interfaz interna | Red Host-only, segmento `192.168.10.0/24` |
| Interfaz de salida | Red puente, con dirección observada `192.168.80.46` durante las pruebas |
| Protocolo | NTP sobre UDP |
| Puerto | `123/udp` |
| Clientes autorizados | `192.168.10.0/24` |
| Zona horaria del servidor | `America/Bogota` |
| Archivo principal | `/etc/chrony/chrony.conf` |
| Servicio systemd | `chrony.service` |

**Flujo de sincronización:**

```text
Servidores NTP públicos
         |
         | NTP / UDP 123
         v
Red externa / interfaz puente
         |
         v
srv-servientrega (Chrony)
192.168.10.10:123/udp
         |
         | NTP / UDP 123
         v
Red interna 192.168.10.0/24
         |
         +-- Estaciones Windows autorizadas
         +-- Estaciones Linux autorizadas
```

La dirección `192.168.80.46` corresponde a una observación del entorno durante las pruebas y puede cambiar al conectarse a otra red. La dirección de servicio para los clientes internos es `192.168.10.10`.

## 4. Implementación y configuración

### 4.1 Instalación y preparación

Se utilizó Chrony como componente de sincronización horaria. Los comandos operativos de instalación y comprobación son:

```bash
sudo apt update
sudo apt install chrony
systemctl status chrony --no-pager -l
```

La ejecución de `chrony.service` se confirmó mediante `systemctl is-active chrony`, con resultado `active`.

### 4.2 Respaldo del archivo principal

Antes de modificar la configuración se generó una copia de respaldo:

```bash
sudo cp /etc/chrony/chrony.conf /etc/chrony/chrony.conf.bak
sudo ls -lh /etc/chrony/chrony.conf*
```

El archivo principal se editó con:

```bash
sudo nano /etc/chrony/chrony.conf
```

### 4.3 Configuración NTP aplicada

Se conservaron las fuentes públicas definidas para Ubuntu y se establecieron las directivas de servicio interno. Las líneas relevantes verificadas fueron:

```conf
pool ntp.ubuntu.com iburst maxsources 4
pool 0.ubuntu.pool.ntp.org iburst maxsources 1
pool 1.ubuntu.pool.ntp.org iburst maxsources 1
pool 2.ubuntu.pool.ntp.org iburst maxsources 2

sourcedir /run/chrony-dhcp
sourcedir /etc/chrony/sources.d
keyfile /etc/chrony/chrony.keys
driftfile /var/lib/chrony/chrony.drift
ntsdumpdir /var/lib/chrony
logdir /var/log/chrony
maxupdateskew 100.0
rtcsync
makestep 1 3
leapsectz right/UTC

allow 192.168.10.0/24
bindaddress 192.168.10.10
port 123
```

**Interpretación de las directivas principales:**

| Directiva | Función |
|---|---|
| `pool ... iburst` | Define las fuentes externas y acelera la obtención inicial de mediciones. |
| `rtcsync` | Facilita la actualización del reloj de hardware desde el reloj del sistema cuando corresponde. |
| `makestep 1 3` | Permite correcciones por salto superiores a un segundo durante las primeras tres actualizaciones del daemon. |
| `allow 192.168.10.0/24` | Autoriza solicitudes NTP de los clientes de la red interna. |
| `bindaddress 192.168.10.10` | Limita la escucha del servicio NTP a la dirección interna especificada. |
| `port 123` | Establece el puerto estándar de NTP. |

Los archivos `README` encontrados en los directorios adicionales de Chrony no introdujeron fuentes adicionales de configuración en las verificaciones realizadas.

### 4.4 Reinicio y activación

Tras guardar los cambios se reinició el servicio y se comprobó su estado:

```bash
sudo systemctl restart chrony
systemctl is-active chrony
sudo systemctl status chrony --no-pager -l
```

**Resultado observado:** `active (running)` y servicio habilitado para iniciarse automáticamente.

### 4.5 Verificación del puerto de escucha

```bash
sudo ss -lunp | grep ':123'
```

**Resultado observado:** proceso `chronyd` asociado a `192.168.10.10:123` mediante UDP.

> **Nota técnica:** NTP utiliza UDP. Una prueba TCP al puerto 123 no constituye una validación del servicio.

## 5. Pruebas y resultados

### 5.1 Estado del servicio

```bash
systemctl is-active chrony
```

**Resultado:** `active`.

### 5.2 Fuentes externas y seguimiento

```bash
chronyc sources -v
chronyc tracking
chronyc activity
```

Durante las pruebas se observaron ocho fuentes en línea, sin fuentes fuera de línea, y selección de referencias NTP públicas. Los indicadores de `chronyc tracking` mostraron finalmente un estrato `3` y `Leap status: Normal`.

Las fuentes seleccionadas pueden cambiar de forma automática; esto es un comportamiento esperado de Chrony.

### 5.3 Autorización de clientes

```bash
sudo chronyc accheck 192.168.10.1
```

**Resultado:** `208 Access allowed`.

Esta comprobación confirma que la dirección del equipo Windows anfitrión está autorizada por las reglas del servidor NTP; no sustituye una prueba de tráfico desde el cliente.

### 5.4 Prueba desde Windows

En Windows PowerShell se ejecutó:

```powershell
w32tm /stripchart /computer:192.168.10.10 /samples:5 /dataonly
```

**Resultado:** cinco muestras de respuesta obtenidas desde `192.168.10.10:123`, con diferencias observadas cercanas a `+0,139` segundos.

La prueba acredita la respuesta NTP del servidor a solicitudes originadas desde el equipo Windows. No implica, por sí sola, que Windows haya cambiado su fuente de sincronización predeterminada.

### 5.5 Sincronización del reloj de Ubuntu

```bash
timedatectl show -p NTPSynchronized -p NTP -p Timezone
chronyc tracking
```

**Resultado final observado en la recuperación:**

```text
Timezone=America/Bogota
NTP=yes
NTPSynchronized=yes
Stratum       : 3
Leap status   : Normal
```

En la misma comprobación, `chronyc tracking` informó una desviación del sistema aproximada de **5,24 ms** y una dispersión raíz de aproximadamente **30,03 ms**.

### 5.6 Seguimiento de incidencias recientes

```bash
sudo journalctl -u chrony --since "3 minutes ago" --no-pager \
  | grep -Ei 'time jump|can.t synchronise' \
  || echo "Sin saltos ni perdidas de sincronizacion recientes"
```

**Resultado comunicado en la verificación final:**

```text
Sin saltos ni perdidas de sincronizacion recientes
```

Este resultado se limita al intervalo consultado. Se interpreta junto con la sincronización confirmada previamente, no como una garantía de estabilidad indefinida.

## 6. Incidencia detectada y tratamiento

### 6.1 Descripción

Durante la puesta en funcionamiento se registraron eventos `Forward time jump detected!` y `Can't synchronise: no selectable sources`. En esos momentos se observaron indicadores como `Reference ID: 00000000`, `Stratum: 0`, `Leap status: Not synchronised` y `NTPSynchronized=no`.

### 6.2 Diagnóstico

Se verificaron los siguientes componentes:

- Resolución DNS de `ntp.ubuntu.com`.
- Conectividad externa mediante `ping`.
- Disponibilidad y respuesta de múltiples fuentes NTP públicas.
- Estadísticas de medición y selección de fuentes con `chronyc`.
- Registros del servicio con `journalctl`.
- Reloj de referencia del kernel y detección del hipervisor.
- Configuración de la máquina virtual en VirtualBox.

El sistema detectó un entorno de virtualización `oracle` y se observaron referencias a los relojes `tsc` y `kvm-clock`. Las pruebas permitieron descartar una falta general de conectividad o de resolución DNS como explicación suficiente de la incidencia.

**Consideración técnica:** los saltos temporales fueron compatibles con un problema de estabilidad del reloj en el entorno virtualizado; las evidencias recopiladas no permiten atribuir una causa raíz única y definitiva.

### 6.3 Recuperación observada

Con posterioridad, Chrony volvió a seleccionar una fuente válida, el reloj del sistema recuperó el estado `NTPSynchronized=yes` y la dispersión raíz disminuyó desde valores transitorios elevados —aproximadamente 57 segundos— hasta cerca de 0,030 segundos.

La consulta final del registro no encontró nuevos saltos ni pérdidas de sincronización en los tres minutos examinados. Por ello se considera recuperada la operación inicial, con seguimiento recomendado.

## 7. Operación y mantenimiento

### 7.1 Comprobación rutinaria

```bash
systemctl is-active chrony
chronyc tracking
chronyc sources -v
chronyc activity
timedatectl status
```

Se espera un servicio activo, una fuente seleccionada (`^*`), un estrato válido, `Leap status: Normal` y `NTPSynchronized=yes` después del periodo normal de estabilización.

### 7.2 Revisión de eventos

```bash
sudo journalctl -u chrony --since "1 hour ago" --no-pager
```

Prestar especial atención a mensajes de salto de tiempo, ausencia de fuentes seleccionables o pérdidas recurrentes de sincronización.

### 7.3 Verificación de la configuración publicada

```bash
sudo grep -E '^(allow|bindaddress|port) ' /etc/chrony/chrony.conf
sudo ss -lunp | grep ':123'
sudo chronyc accheck 192.168.10.1
```

### 7.4 Reinicio controlado

Solo si existe una necesidad operativa y tras revisar los registros:

```bash
sudo systemctl restart chrony
systemctl is-active chrony
chronyc tracking
```

La sincronización puede tardar un intervalo en recuperarse después de reiniciar el servicio.

### 7.5 Respaldo y reversión

El respaldo creado es `/etc/chrony/chrony.conf.bak`. En caso de requerirse una reversión autorizada:

```bash
sudo cp /etc/chrony/chrony.conf.bak /etc/chrony/chrony.conf
sudo systemctl restart chrony
```

**Advertencia:** restaurar la configuración previa puede retirar la autorización de clientes y la escucha en la IP interna; se debe comprobar nuevamente el servicio antes de considerarlo operativo.

## 8. Consideraciones y limitaciones

1. **Virtualización:** el reloj de una máquina virtual puede verse afectado por pausas, suspensión, carga del anfitrión y mecanismos de temporización del hipervisor. Es recomendable revisar la sincronización tras cada reinicio o suspensión.
2. **Dependencia de Internet:** el servidor utiliza fuentes públicas externas. Una interrupción prolongada puede degradar la precisión temporal; no se configuró una fuente de referencia local independiente.
3. **Red interna:** el servicio se publica en `192.168.10.10` y autoriza únicamente la subred `192.168.10.0/24` según la configuración comprobada.
4. **Clientes:** cada estación deberá configurarse para utilizar `192.168.10.10` como fuente NTP si se requiere sincronización permanente con el servidor interno.
5. **Monitoreo:** una consulta de registros sin incidencias recientes no equivale a una prueba de estabilidad de larga duración.
6. **Zona horaria:** NTP distribuye una referencia temporal común; la presentación de la hora local depende de la zona horaria configurada en cada cliente.

## 9. Evidencias de implementación

Las evidencias visuales del servicio NTP se organizan en la carpeta `AdminTI/capturas/`, siguiendo la numeración consecutiva del expediente técnico de infraestructura. Las capturas 01 a 14 corresponden a componentes documentados previamente; las evidencias específicas de NTP son las siguientes:

| Archivo de evidencia | Contenido verificable | Registro documental |
|---|---|---|
| `15-validacion-ntp-cliente-windows.png` | Conectividad entre el anfitrión Windows y la máquina virtual Ubuntu; respuestas del servidor NTP obtenidas mediante `w32tm /stripchart /computer:192.168.10.10 /samples:5 /dataonly`. | Captura guardada. |
| `16-configuracion-servicio-ntp.png` | Identificación de `srv-servientrega`, IP interna `192.168.10.10`, directivas de Chrony (`pool`, `allow`, `bindaddress`, `port`, `makestep`, `rtcsync`), servicio `active` y `enabled`, escucha en UDP 123 y autorización `208 Access allowed` para `192.168.10.1`. | Captura prevista; guardar después de comprobar los resultados. |
| `17-validacion-final-ntp.png` | `NTPSynchronized=yes`, `NTP=yes`, zona horaria `America/Bogota`, referencia y estrato válidos, `Leap status: Normal`, fuente seleccionada (`^*`), servicio activo y consulta de eventos recientes sin incidencias. | Captura prevista; guardar únicamente con resultados satisfactorios. |

### 9.1 Correspondencia de las evidencias con las pruebas

- **Captura 15:** respalda la prueba funcional desde Windows descrita en el apartado **5.4**.
- **Captura 16:** respalda la configuración del apartado **4.3**, la activación del apartado **4.4**, la escucha del apartado **4.5** y la autorización del apartado **5.3**.
- **Captura 17:** respalda las comprobaciones de fuentes y seguimiento del apartado **5.2**, la sincronización del apartado **5.5** y la revisión de eventos del apartado **5.6**.

### 9.2 Ubicación y conservación

```text
AdminTI/
└── capturas/
    ├── 15-validacion-ntp-cliente-windows.png
    ├── 16-configuracion-servicio-ntp.png
    └── 17-validacion-final-ntp.png
```

Las capturas deben mostrar las salidas reales de las comprobaciones, con suficiente legibilidad y sin alterar los resultados. **La asignación de un nombre de archivo no constituye por sí sola evidencia de que la imagen se haya generado o guardado.** Las capturas 16 y 17 se incorporarán físicamente al expediente cuando se completen sus verificaciones.

## 10. Conclusión

Se implementó y verificó un servicio NTP interno con Chrony en `srv-servientrega`, accesible mediante `192.168.10.10:123/udp` para la red autorizada `192.168.10.0/24`. Las comprobaciones incluyeron la respuesta a solicitudes desde Windows, el acceso a fuentes NTP externas y la recuperación de la sincronización del reloj de Ubuntu.

La incidencia de saltos temporales observada durante la puesta en funcionamiento no volvió a aparecer en la última ventana de registros consultada. El servicio se considera **funcional y apto para la operación inicial**, sujeto al monitoreo habitual recomendado para entornos virtualizados.

---

**Fin del documento técnico — Servicio NTP con Chrony.**
