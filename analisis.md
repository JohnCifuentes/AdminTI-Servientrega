# Proyecto final: Administración de Infraestructura de TI
## Análisis, diseño y consolidación de la implementación

**Institución:** Universidad del Quindío  
**Asignatura:** Administración de Infraestructura de TI  
**Organización de referencia:** Servientrega S.A.  
**Escenario:** sede operativa colombiana **simulada**, con nueve perfiles de personal previstos  
**Corte documental:** 19 de noviembre de 2026 (con pruebas de integración registradas el 20 de noviembre de 2026, según la hora mostrada en los resultados)  
**Estado:** infraestructura implementada y validada en laboratorio; cumplimiento parcial de los requisitos de HTTPS y despliegue web mediante Dokploy.

> **Alcance de la revisión:** este documento actualiza el análisis original a partir de los diez documentos técnicos `infraestructura/01` a `10` y del inventario de 32 nombres de capturas facilitado por el equipo. Los archivos de imagen y el código fuente no fueron adjuntados en esta revisión: su existencia y contenido visual se consignan como **reportados**, no como inspeccionados. El archivo `diagrama.mmd` tampoco se adjuntó para verificar su versión actual.

## 1. Objetivo y alcance

Diseñar, implementar y validar una infraestructura de laboratorio sobre Oracle VirtualBox y Ubuntu Server para una sede operativa simulada de Servientrega S.A. de cinco a diez empleados. La solución centraliza servicios de red, sincronización horaria, compartición de archivos, cuentas Linux, impresión, administración de contenedores, base de datos y un portal institucional básico.

**Resultado alcanzado:** servidor y cliente Ubuntu, Windows como anfitrión/cliente, DNS con dnsmasq, NTP con Chrony, NFS, NIS, CUPS, Samba, Docker/Dokploy, MySQL y portal Flask integrados funcionalmente. El portal usa dos perfiles de demostración y consulta MySQL; no implementa autenticación web real ni operaciones logísticas.

**Límites relevantes:** el portal se publicó por HTTP en Docker CLI, **no** como aplicación gestionada desde Dokploy; **HTTPS/TLS no fue configurado**. Dokploy sí administra el servicio MySQL. No se utilizan datos corporativos reales ni se representa la infraestructura oficial de Servientrega.


## 2. Contexto y necesidades de la sede simulada

La sede simulada realiza recepción de paquetes, atención al cliente, clasificación, coordinación operativa y tareas administrativas. Estas actividades motivan las siguientes necesidades:

| ID | Necesidad | Justificación empresarial |
|---|---|---|
| NT-01 | Acceso a portal institucional | Brindar un punto de acceso web básico para los empleados. |
| NT-02 | Gestión centralizada de aplicaciones | Simplificar despliegues y administración. |
| NT-03 | Archivos compartidos Linux | Facilitar el intercambio de documentos operativos entre clientes Linux. |
| NT-04 | Archivos compartidos Windows | Facilitar el intercambio de documentos entre estaciones Windows y el servidor. |
| NT-05 | Usuarios Linux centralizados | Administrar cuentas de laboratorio en un servidor. |
| NT-06 | Impresión compartida | Centralizar una cola de impresión de documentos de prueba. |
| NT-07 | Sincronización horaria | Mantener coherencia temporal en los equipos. |
| NT-08 | Base de datos | Demostrar la administración de una base de datos conectada al portal. |
| NT-09 | Acceso seguro y nombres internos | Publicar el portal mediante HTTPS y resolver nombres en la LAN. |

## 3. Requerimientos funcionales aprobados y trazabilidad final

Se conserva el texto aprobado de los requerimientos. La columna de evaluación indica únicamente lo respaldado por los documentos y pruebas reportadas.

| ID | Requerimiento aprobado | Evaluación | Resultado y referencia |
|---|---|---|---|
| RF-01 | Permitir el acceso al portal institucional de la sede mediante HTTPS. | **No cumplido íntegramente** | Portal accesible por HTTP `:5000` y `:5001`; no se configuró TLS. Documento 10. |
| RF-02 | Mostrar un mensaje de bienvenida diferente según el tipo de usuario o rol que acceda al portal. | **Cumplido como demostración** | Perfiles `administrador` y `operador`, mensajes recuperados de MySQL; no existe autenticación real. Documentos 09–10. |
| RF-03 | Disponer de una base de datos mediante Dokploy y establecer su conexión con la aplicación web. | **Cumplido** | MySQL 8.4 en Dokploy; Flask/PyMySQL con `/health/db` HTTP 200 y consulta de perfiles. Documentos 09–10. |
| RF-04 | Permitir el despliegue y administración del portal web mediante Dokploy. | **Pendiente** | Portal construido y ejecutado con Docker CLI; no se registró como aplicación Dokploy. Documento 10. |
| RF-05 | Permitir compartir archivos mediante NFS entre equipos Linux. | **Cumplido en el alcance probado** | Montajes NFSv4.2 y transferencia remota en recurso común. Documento 05. |
| RF-06 | Permitir acceder a carpetas compartidas mediante Samba desde equipos Windows. | **Cumplido** | Acceso autenticado y escritura Windows ↔ Ubuntu. Documento 08. |
| RF-07 | Centralizar las cuentas de prueba Linux mediante NIS. | **Cumplido en laboratorio** | Resolución de cuenta y autenticación en cliente Ubuntu; aislamiento externo pendiente de verificar. Documento 06. |
| RF-08 | Administrar trabajos de impresión mediante CUPS. | **Cumplido** | Cliente Ubuntu envió trabajo a cola PDF; archivo PDF generado en servidor. Documento 07. |
| RF-09 | Mantener sincronizados los relojes de los clientes mediante NTP. | **Cumplido en las pruebas registradas** | Chrony activo, respuesta a Windows y sincronización recuperada; vigilar estabilidad del reloj virtual. Documento 04. |
| RF-10 | Gestionar aplicaciones y servicios desplegados mediante Dokploy. | **Parcial** | Dokploy operativo y MySQL gestionado; portal web permanece fuera de Dokploy. Documentos 02, 09 y 10. |

### 3.1. Alcance real del portal

- Portal HTML/CSS con backend Flask 3.1.1 y Gunicorn 23.0.0, empaquetado en Docker.
- Dos perfiles demostrativos: **Administrador** y **Operador**. Los cinco perfiles previstos en el diseño inicial no se implementaron como roles web independientes.
- La versión 1.0 muestra mensajes definidos en Python, puerto `5000`.
- La versión 2.0 consulta `servientrega_db.perfiles` mediante PyMySQL 1.1.1, puerto `5001`; `/health` y `/health/db` respondieron HTTP 200.
- La selección `?rol=` es una demostración de presentación, **no un mecanismo de identidad o control de acceso**.
- No hay gestión de envíos, usuarios corporativos reales, TLS ni despliegue del portal en Dokploy.


## 4. Requerimientos no funcionales aprobados

| ID | Requerimiento | Descripción |
|---|---|---|
| RNF-01 | Seguridad de acceso | Los servicios y recursos compartidos deben contar con mecanismos de control de acceso y permisos. |
| RNF-02 | Comunicación segura | El portal institucional debe permitir conexiones mediante HTTPS. |
| RNF-03 | Disponibilidad | Los servicios implementados deben permanecer activos y accesibles durante las pruebas de funcionamiento. |
| RNF-04 | Compatibilidad | La infraestructura debe permitir la interacción entre equipos Windows y Linux. |
| RNF-05 | Rendimiento | Los recursos del servidor deben ser suficientes para soportar los servicios y usuarios definidos en el escenario. |
| RNF-06 | Centralización | La administración de los servicios de infraestructura debe realizarse desde el servidor Ubuntu y Dokploy, según corresponda. |
| RNF-07 | Integridad de la información | Los archivos compartidos y los datos almacenados en la base de datos deben conservar su integridad. |
| RNF-08 | Sincronización | Los equipos clientes deben mantener una referencia horaria común mediante NTP. |
| RNF-09 | Mantenibilidad | Los servicios deben contar con configuraciones documentadas que faciliten su administración y mantenimiento. |
| RNF-10 | Escalabilidad | La infraestructura debe permitir incorporar nuevos usuarios y recursos sin requerir un rediseño completo. |

### 4.1. Evaluación de los requisitos no funcionales

| ID | Evaluación | Observación |
|---|---|---|
| RNF-01 | Parcial | Controles de permisos y restricciones documentados en NFS, NIS, Samba, CUPS y MySQL; no hay autenticación web real ni auditoría integral. |
| RNF-02 | Pendiente | Portal HTTP; HTTPS no implementado. |
| RNF-03 | Verificado durante pruebas | Servicios y contenedores activos en las comprobaciones; no implica alta disponibilidad. |
| RNF-04 | Cumplido en laboratorio | Acceso Windows a Samba y portal; cliente Ubuntu a NFS, NIS y CUPS. |
| RNF-05 | Parcialmente verificado | VM operó con 2 vCPU, 8 GB y 50 GB; no se documentó prueba de carga con nueve usuarios simultáneos. |
| RNF-06 | Parcial | Ubuntu centraliza servicios y Dokploy administra MySQL; Flask se administra por Docker CLI. |
| RNF-07 | Parcialmente verificado | Escritura/lectura NFS y Samba, consultas SQL y volumen MySQL; no consta prueba de restauración ni ensayo de fallos. |
| RNF-08 | Verificado en pruebas | Chrony respondió a cliente Windows; observar estabilidad tras reinicios. |
| RNF-09 | Cumplido documentalmente | Diez documentos técnicos con procedimientos y resultados; falta inspección de las capturas originales. |
| RNF-10 | No probado | Arquitectura ampliable en principio, sin prueba de escalabilidad o capacidad. |


## 5. Justificación y criterios de éxito por servicio

| Servicio | Necesidad | Resultado comprobado / límite | Documento |
|---|---|---|---|
| VirtualBox + Ubuntu | Plataforma base | Servidor `srv-servientrega` y cliente Ubuntu; redes Bridged/Host-only/NAT según equipo. | [01](infraestructura/01-virtualbox-ubuntu-server.md) |
| Docker / Dokploy | Contenedores y administración | Docker Swarm y panel Dokploy activos; MySQL gestionado. | [02](infraestructura/02-docker-dokploy.md) |
| DNS / dnsmasq | Nombres internos | Resolución de `servientrega.lab` y registros de laboratorio, con pruebas Ubuntu/Windows; DNS no distribuido automáticamente por DHCP. | [03](infraestructura/03-servicio-dns-dnsmasq.md) |
| NTP / Chrony | Tiempo común | Servidor UDP 123, pruebas Windows y recuperación de sincronización. | [04](infraestructura/04-servicio-ntp-chrony.md) |
| NFS | Archivos Linux | Tres exportaciones montadas en Ubuntu cliente; lectura/escritura remota validada en recurso común. | [05](infraestructura/05-servicio-nfs.md) |
| NIS | Identidades Linux | Cuenta ficticia autenticada desde Ubuntu; protocolo heredado restringido al laboratorio. | [06](infraestructura/06-servicio-nis.md) |
| CUPS | Impresión | Cola `PDF` compartida; impresión remota y PDF generado. | [07](infraestructura/07-servicio-cups.md) |
| Samba | Archivos Windows | Recurso `compartido`, acceso y escritura desde Windows. | [08](infraestructura/08-servicio-samba.md) |
| MySQL | Datos del portal | MySQL 8.4 en Dokploy; `servientrega_db.perfiles`, conexión privada y consultas autenticadas. | [09](infraestructura/09-servicio-mysql.md) |
| Portal Flask | Acceso institucional | HTML/CSS y dos perfiles; integración SQL real en Docker, HTTP 5001; sin HTTPS ni despliegue web Dokploy. | [10](infraestructura/10-portal-web-flask.md) |

**Decisión de alcance:** se implementaron los cinco servicios Linux tradicionales NTP, NFS, NIS, CUPS y Samba, además de DNS, base de datos y web. El servidor web final es **Flask/Gunicorn**, no Nginx/Apache como se propuso inicialmente; esta diferencia debe contrastarse con la rúbrica académica.


## 6. Inventario de usuarios

| Perfil | Cantidad | Uso previsto |
|---|---:|---|
| Administrador de sede | 1 | Supervisión y consulta institucional. |
| Atención al cliente | 2 | Acceso a portal y recursos autorizados. |
| Personal logístico | 3 | Documentos operativos e impresión. |
| Personal administrativo | 2 | Archivos y documentos compartidos. |
| Administrador TI | 1 | Gestión de infraestructura. |
| **Total** | **9** | **Usuarios ficticios del escenario.** |

Estos nueve usuarios son perfiles del escenario; no requieren nueve equipos físicos ni nueve sesiones simultáneas durante la demostración.

## 7. Inventario de infraestructura implementada

| ID | Recurso | Cantidad | Especificación observada |
|---|---|---:|---|
| HOST-01 | Portátil Windows 11 | 1 | HP Laptop 14-ep1xxx, Intel Core Ultra 5 125H, 32 GB RAM, VirtualBox 7.2.22. |
| VM-01 | Servidor Ubuntu | 1 | `srv-servientrega`, Ubuntu Server 24.04.5 LTS, **2 vCPU**, 8 GB RAM, disco VDI 50 GB. |
| VM-02 | Cliente Ubuntu | 1 | `client-nfs`, Ubuntu Server 24.04 LTS; IP interna `192.168.10.20`; se reutilizó para NFS, NIS y CUPS. |
| NET-01 | Red Host-only | 1 | `192.168.10.0/24`, servidor `192.168.10.10`, cliente Linux `192.168.10.20`, Windows `192.168.10.1`. |
| NET-02 | Red Bridged | 1 | Servidor `enp0s3`, IP DHCP observada `192.168.80.46`, puerta de enlace `192.168.80.1`. |
| NET-03 | NAT de cliente | 1 | Cliente Ubuntu `enp0s3`, IP observada `10.0.2.15`. |
| PRN-01 | Impresora PDF virtual | 1 | Cola CUPS `PDF`; no se utilizó impresora física. |
| SW-01 | Plataforma Docker/Dokploy | 1 | Docker Engine, Docker Swarm, Dokploy 0.31.4, Traefik y PostgreSQL interno. |
| DB-01 | MySQL | 1 | Imagen `mysql:8.4`, versión SQL 8.4.13, volumen persistente y red `dokploy-network`. |
| APP-01 | Portal Flask | 2 contenedores de validación | Versión 1.0 en `:5000` y versión 2.0 con MySQL en `:5001`; contenedores Docker independientes. |

**Diferencias respecto al diseño inicial:** el servidor se implementó con **2 vCPU**, no cuatro; el cliente Linux es **Ubuntu Server**, no Ubuntu Desktop; su IP es **`192.168.10.20`**, no `192.168.10.101`. Los nueve usuarios del escenario son perfiles de negocio, no nueve cuentas NIS ni nueve sesiones web verificadas.


## 8. Arquitectura y redes

**Topología validada:** Windows 11 y las dos VM Ubuntu se comunican por Host-only `192.168.10.0/24`. El servidor tiene una interfaz Bridged hacia la red física; el cliente Ubuntu utiliza NAT para salida externa. Los servicios Linux tradicionales se publican en la red interna con restricciones específicas. Docker Swarm/Dokploy gestiona MySQL; Flask se ejecuta por Docker CLI y comparte la red overlay `dokploy-network` para consultar MySQL.

### 8.1. Interfaces y direccionamiento comprobado

| Equipo | Interfaz | Modo | IP observada | Función |
|---|---|---|---|---|
| `srv-servientrega` | `enp0s3` | Bridged | `192.168.80.46/24` (DHCP) | Red física / Internet. |
| `srv-servientrega` | `enp0s8` | Host-only | `192.168.10.10/24` (estática) | Servicios internos. |
| `client-nfs` | `enp0s3` | NAT | `10.0.2.15/24` (observada) | Descargas / salida externa. |
| `client-nfs` | `enp0s8` | Host-only | `192.168.10.20/24` | Cliente Linux de servicios. |
| Windows 11 | VirtualBox Host-only | Host-only | `192.168.10.1/24` | Administración SSH y validación web/SMB. |

La dirección Bridged depende del DHCP de la red física; no debe considerarse fija. Host-only no utiliza gateway predeterminado.

### 8.2. Redes de contenedores

- `dokploy-network`: Docker overlay, ámbito Swarm, `Attachable: true`.
- MySQL: servicio `servientrega-mysql-do9ws9`, accesible internamente por DNS Docker y TCP `3306`.
- Portal 1.0: contenedor `portal-servientrega`, puerto del host `192.168.10.10:5000`.
- Portal 2.0: contenedor `portal-servientrega-test`, unido a `dokploy-network`, puerto del host `192.168.10.10:5001`.
- Se validó resolución DNS del servicio MySQL y conexión TCP desde el contenedor Flask. El puerto MySQL no quedó publicado en el host durante la comprobación.

### 8.3. Dominio interno y acceso web

- Zona interna `servientrega.lab`, atendida por dnsmasq en `192.168.10.10:53`.
- Registros documentados: `servientrega.lab`, `srv-servientrega.servientrega.lab`, `dokploy.servientrega.lab` y `www.servientrega.lab` → `192.168.10.10`.
- El acceso final probado al portal se realizó mediante **IP y HTTP**, no por un nombre HTTPS.
- No consta emisión ni instalación de certificado TLS para el portal.
- DNS interno no implica automáticamente un dominio público, y la resolución por defecto en Windows no fue modificada de forma global.


## 9. Matriz técnica: IP, puerto, protocolo y tipo de servicio

| Servicio | Dirección / red | Puerto | Protocolo | Estado y exposición |
|---|---|---|---|---|
| SSH | `192.168.10.10` | 22 | TCP | Acceso administrativo probado desde Windows. |
| Dokploy | `192.168.10.10` | 3000 | HTTP/TCP | Panel accesible desde Windows; sin HTTPS documentado. |
| DNS / dnsmasq | `192.168.10.10` | 53 | UDP/TCP | Servicio interno con consultas validadas. |
| NTP / Chrony | `192.168.10.10` | 123 | UDP | Servicio interno y prueba desde Windows. |
| NFSv4.2 | `192.168.10.10` | 2049 | TCP | Exportaciones a `192.168.10.0/24`. |
| RPC / rpcbind | Servidor Ubuntu | 111 | TCP/UDP | Dependencia RPC compartida; revisar restricciones efectivas. |
| NIS / ypserv | Servidor Ubuntu | 834 | TCP/UDP | Puerto fijo y reglas de protección documentadas. |
| CUPS / IPP | `192.168.10.10` | 631 | TCP | Cola PDF compartida a cliente Ubuntu. |
| Samba / SMB | `192.168.10.10` | 445, 139 | TCP | Servicio restringido a interfaz interna; acceso Windows validado. |
| MySQL | `dokploy-network` | 3306 | TCP | Solo red interna Docker en las pruebas; no publicado al host. |
| Flask 1.0 | `192.168.10.10` | 5000 | HTTP/TCP | Portal inicial, mensajes estáticos. |
| Flask 2.0 | `192.168.10.10` | 5001 | HTTP/TCP | Portal con consultas reales a MySQL. |
| HTTPS previsto | `192.168.10.10` | 443 | TLS/TCP | **No implementado para el portal**. |

Los puertos son los efectivamente identificados o documentados para cada servicio, no una auditoría de todos los sockets del sistema. El funcionamiento de Traefik dentro de Dokploy no constituye por sí solo una publicación HTTPS del portal.


## 10. Controles básicos de seguridad y límites

1. Cuentas de prueba ficticias y sin datos corporativos reales; NIS es un protocolo heredado no apto para identidades de producción.
2. NFS con exportaciones restringidas a `192.168.10.0/24` y `root_squash`; permisos departamentales UNIX documentados.
3. Samba con usuario dedicado, permisos de directorio, interfaces restringidas y SMB2 mínimo.
4. CUPS publicado en IP Host-only y con reglas de acceso a la red interna.
5. NIS con puerto `834` y protección por reglas; queda pendiente una prueba concluyente del aislamiento desde la red externa.
6. MySQL con credenciales independientes, volumen persistente, conexión por red Docker privada y sin publicación del puerto 3306 al host en la validación.
7. Flask utiliza variables de entorno para MySQL; `.env` tiene permisos `600` y está excluido del contexto Docker. **No incorporar `.env` al repositorio ni a las evidencias.**
8. La selección de perfiles por parámetro URL **no autentica ni autoriza usuarios**.
9. La publicación web es HTTP; no afirmar confidencialidad de transporte ni cumplimiento TLS.
10. No se ha realizado una auditoría integral de seguridad, restauración de respaldos ni prueba de carga.


## 11. Plan de pruebas y trazabilidad ejecutada

| Requisito | Prueba documentada | Evidencias reportadas | Resultado |
|---|---|---|---|
| RF-01 | Acceso al portal desde Windows | 28, 29, 32 | Acceso HTTP correcto; **HTTPS pendiente**. |
| RF-02 | Selección de dos perfiles y mensajes diferenciados | 28, 29, 32 | Validado como demostración, sin autenticación. |
| RF-03 | MySQL autenticado, tabla `perfiles`, `/health/db` y consultas Flask | 30, 31, 32 | Validado. |
| RF-04 | Aplicación Flask visible como recurso de Dokploy | Ninguna | No implementado. |
| RF-05 | Exportaciones, montajes y lectura/escritura NFS | 18, 19, 20 | Validado en el recurso común. |
| RF-06 | Acceso SMB desde Windows y verificación en Ubuntu | 25, 26, 27 | Validado. |
| RF-07 | Cuenta NIS autenticada en Ubuntu cliente | 21, 22 | Validado en LAN; aislamiento externo sin prueba final. |
| RF-08 | Impresión remota y PDF generado | 23, 24 | Validado. |
| RF-09 | Configuración Chrony y pruebas de cliente | 15, 16, 17 | Validado durante pruebas; vigilar saltos de reloj virtual. |
| RF-10 | Panel Dokploy y MySQL desplegado | 10, 11, 12, 31 | Plataforma y BD validadas; web no gestionada allí. |

**Importante:** las referencias numéricas son nombres facilitados por el usuario. Las imágenes originales no fueron adjuntadas en esta revisión, por lo que no se ha auditado su contenido visual ni se puede asegurar que todas estén físicamente presentes en `capturas/`.


## 12. Riesgos, diferencias respecto al diseño y trabajo no ejecutado

| Tema | Situación al cierre | Implicación |
|---|---|---|
| HTTPS/TLS | No configurado | RF-01 y RNF-02 pendientes; el criterio web HTTPS de la guía no está satisfecho. |
| Portal en Dokploy | Contenedor Docker CLI, no aplicación Dokploy | RF-04 pendiente; RF-10 parcial. |
| Tecnología web | Flask/Gunicorn en vez de Nginx/Apache | Desviación frente a la propuesta y la categoría de servidor web del enunciado; justificar o consultar con la profesora. |
| Roles web | Dos perfiles demostrativos en vez de los cinco roles propuestos | RF-02 satisfecho como mensajes diferenciados, no como autenticación o perfiles completos. |
| VM principal | 2 vCPU, 8 GB, 50 GB | Cumple el mínimo de recursos indicado en la guía; corregir diagramas que aún muestren 4 vCPU. |
| Cliente Linux | Ubuntu Server `192.168.10.20`, no Ubuntu Desktop `.101` | Actualizar topología y tablas. |
| NIS | Protocolo heredado y prueba externa pendiente | Mantener únicamente en laboratorio aislado. |
| NTP | Se observaron saltos de reloj en la virtualización | Supervisar después de reinicios; no prometer sincronización permanente. |
| DNS | Zona interna, sin DHCP que la distribuya | La resolución requiere configurar cliente o consulta explícita; no equivale a dominio público. |
| NFS | No se ensayó remotamente acceso cruzado entre departamentos ni `root_squash` | Limitar conclusiones a montajes y transferencia común efectivamente probados. |
| Respaldo y recuperación | Volumen MySQL persistente; sin restauración probada | Persistencia no demuestra recuperación ante pérdida. |
| Documentación y evidencias | Diez documentos disponibles; capturas solo inventariadas | Revisar archivos de imagen y coherencia de referencias antes de entrega. |

**Decisión de cierre técnico:** no se ejecutarán nuevas configuraciones por defecto. Los puntos pendientes se informan con transparencia y deben evaluarse frente a los criterios de la profesora antes de declarar cumplimiento total.


## 13. Diagrama de arquitectura

El diagrama editable previsto es [`diagrama.mmd`](diagrama.mmd). **No se adjuntó a esta revisión**, por lo que no se puede confirmar que represente la topología definitiva. Antes de entregar, verificar que muestre:

- Windows Host-only `192.168.10.1`, servidor `192.168.10.10` y cliente Ubuntu `192.168.10.20`.
- Interfaz Bridged del servidor y NAT del cliente Linux.
- Servicios DNS, NTP, NFS, NIS, CUPS y Samba en Ubuntu.
- Dokploy/Swarm administrando MySQL; portal Flask en Docker CLI conectado a `dokploy-network`.
- Portal HTTP `:5001` y ausencia de TLS en la implementación validada.

No representar Nginx, certificados HTTPS ni un despliegue web de Dokploy como componentes ya implementados.


## 14. Inventario de evidencias y documentos

### 14.1. Capturas reportadas

Se relacionan los **32 nombres** comunicados por el equipo, sin suponer una extensión específica. Para enlazarlos en Markdown se debe verificar si los archivos son `.png`, `.jpg` u otro formato.

| N.º | Nombre base reportado | Componente |
|---|---|---|
| 00 | `00-configuracion-virtualbox` | VirtualBox / Ubuntu |
| 01 | `01-inventario-servidor` | VirtualBox / Ubuntu |
| 02 | `02-configuracion-red` | VirtualBox / Ubuntu |
| 03 | `03-pruebas-conectividad` | VirtualBox / Ubuntu |
| 04 | `04-administracion-ssh` | VirtualBox / Ubuntu |
| 05 | `05-configuracion-horaria` | VirtualBox / Ubuntu |
| 06 | `06-estado-mantenimiento` | VirtualBox / Ubuntu |
| 08 | `08-prerrequisitos-docker-dokploy` | Docker / Dokploy |
| 09 | `09-instalacion-docker-dokploy` | Docker / Dokploy |
| 10 | `10-docker-swarm-servicios` | Docker / Dokploy |
| 11 | `11-acceso-dokploy` | Docker / Dokploy |
| 12 | `12-validacion-final-docker-dokploy` | Docker / Dokploy |
| 13 | `13-validacion-dns-interno` | DNS |
| 14 | `14-validacion-final-dns` | DNS |
| 15 | `15-validacion-ntp-cliente-windows` | NTP |
| 16 | `16-configuracion-servicio-ntp` | NTP |
| 17 | `17-validacion-final-ntp` | NTP |
| 18 | `18-nfs-validacion-remota-cliente-servidor` | NFS |
| 19 | `19-nfs-estado-servicio-exportaciones` | NFS |
| 20 | `20-nfs-montajes-remotos-cliente` | NFS |
| 21 | `21-autenticacion-usuario-nis-cliente` | NIS |
| 22 | `22-persistencia-servicio-nis-servidor-cliente` | NIS |
| 23 | `23-cups-impresion-desde-cliente` | CUPS |
| 24 | `24-cups-pdf-generado-servidor` | CUPS |
| 25 | `25-samba-acceso-windows` | Samba |
| 26 | `26-samba-escritura-windows` | Samba |
| 27 | `27-samba-verificacion-ubuntu` | Samba |
| 28 | `28-portal-web-administrador` | Portal Flask |
| 29 | `29-portal-web-operador` | Portal Flask |
| 30 | `30-mysql-validacion-consultas` | MySQL |
| 31 | `31-mysql-servicio-activo-dokploy` | MySQL |
| 32 | `32-portal-flask-mysql-integracion` | Integración Flask–MySQL |

**Observaciones de consistencia:**

- La secuencia informada salta del `06` al `08`: **no se recibió una captura `07`**. No se renumeran los archivos existentes; confirmar si fue descartada o falta adjuntarla.
- El documento `03-servicio-dns-dnsmasq.md` menciona capturas con nombres internos `01-` a `09-` que **no coinciden** con el inventario definitivo `13-` y `14-`; corregir las referencias en ese documento o aclarar que se trata de una numeración antigua.
- El documento `01-virtualbox-ubuntu-server.md` propone una carpeta `capturas/virtualbox-ubuntu/`, mientras el inventario actual parece centralizado en `capturas/`; uniformar las rutas sin duplicar imágenes.
- No se han recibido las imágenes originales; los nombres reportados no prueban por sí solos la ejecución técnica.

### 14.2. Documentos técnicos

Los documentos de implementación se conservan **independientes**, en `AdminTI/infraestructura/`, con nombres `01-virtualbox-ubuntu-server.md` a `10-portal-web-flask.md` según los enlaces de la sección 5. Este `analisis.md` consolida decisiones y resultados, pero **no sustituye** las instrucciones técnicas de cada servicio.

### 14.3. Entregables de repositorio por verificar

- `diagrama.mmd`: comprobar correspondencia con la topología final.
- `codigo/`: el documento 10 indica que el código vive en `/home/adminserv/portal-servientrega/`; **no se verificó** una copia limpia en la carpeta de entrega. No incorporar `.env`.
- `capturas/`: comprobar presencia real, extensiones y calidad visual de los 32 nombres reportados.
- `README.md` y documentación integradora solicitada en la guía: confirmar su preparación; los diez documentos técnicos ya cubren la documentación por servicio, pero no se ha comprobado el empaquetado final exigido por la profesora.


## 15. Conclusión del análisis actualizado

La infraestructura del laboratorio quedó funcional y se demostraron interacciones reales entre clientes Windows/Linux, servicios tradicionales y contenedores. El resultado más relevante de integración es el portal Flask 2.0 que consulta MySQL desplegado en Dokploy mediante una red Docker privada.

**No se declara cumplimiento académico total:** HTTPS/TLS, el despliegue del portal desde Dokploy y la correspondencia estricta con Nginx/Apache permanecen como diferencias frente a la propuesta/rúbrica. Se recomienda entregar esta situación de forma explícita, junto con los resultados comprobados, y confirmar con la profesora si dichas diferencias son aceptables.
