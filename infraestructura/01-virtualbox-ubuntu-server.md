# Implementación del servidor virtual Ubuntu Server

**Infraestructura de TI — Sede operativa simulada de Servientrega S. A.**  
**Documento:** `01-virtualbox-ubuntu-server.md`  
**Componente:** Plataforma de virtualización y sistema operativo base  
**Fecha de implementación y validación:** noviembre de 2026

---

## 1. Propósito

Documentar la implementación y verificación de un servidor virtual Linux que constituya la plataforma base de los servicios de infraestructura de la sede operativa simulada de Servientrega. Se describen el entorno anfitrión, la instalación y configuración de Oracle VirtualBox, la creación de la máquina virtual, la instalación de Ubuntu Server, el direccionamiento de red, la administración remota y las pruebas efectuadas.

Este documento delimita exclusivamente la **plataforma de virtualización y el sistema operativo base**. La instalación y configuración de Docker, Dokploy, DNS interno, servidor web, NTP para clientes, NFS, NIS, CUPS, Samba y MySQL se documentan de manera independiente.

## 2. Alcance y resultado de la implementación

Se implementó la máquina virtual `srv-servientrega` sobre un equipo anfitrión con Windows 11. El servidor utiliza Ubuntu Server 24.04.5 LTS y dos interfaces de red virtuales: una conectada en modo puente a la red física y otra en modo solo-anfitrión para la comunicación privada con Windows y futuros clientes del laboratorio.

**Resultado verificado:** Ubuntu inicia desde su disco virtual, acepta el inicio de sesión del usuario `adminserv`, conserva el direccionamiento de ambas interfaces, alcanza Internet, resuelve nombres externos y permite una sesión SSH desde PowerShell de Windows a `192.168.10.10`.

## 3. Inventario de infraestructura

### 3.1. Equipo anfitrión

| Característica | Valor identificado |
|---|---|
| Fabricante y familia | HP Laptop 14-ep1xxx |
| Sistema operativo | Microsoft Windows 11 Home Single Language, 64 bits |
| Versión de Windows observada | 10.0.26300, compilación 26300 |
| Procesador | Intel Core Ultra 5 125H |
| Núcleos / procesadores lógicos | 14 / 18 |
| Memoria física instalada | 32 GB |
| Almacenamiento | SSD NVMe; disponibilidad declarada de al menos 100 GB antes de la creación de la VM |
| Adaptador de red física utilizado | Realtek RTL8852BE Wi-Fi 6 802.11ax PCIe Adapter |
| Virtualización del procesador | Habilitada, según Administrador de tareas de Windows |
| Seguridad basada en virtualización | Activa en el anfitrión durante las verificaciones iniciales |

El entorno se ejecuta sobre un único portátil; **no requiere un router ni un switch físicos adicionales** para la red privada de VirtualBox. El acceso en puente aprovecha la conexión Wi-Fi existente y la red Host-only es proporcionada por VirtualBox.

### 3.2. Software de virtualización

| Componente | Configuración implementada |
|---|---|
| Hipervisor | Oracle VirtualBox |
| Versión verificada | 7.2.22 r175245 (Qt 6.8.0 en Windows) |
| Nombre de máquina virtual | `srv-servientrega` |
| Sistema operativo invitado | Ubuntu Server 24.04.5 LTS, arquitectura AMD64 |
| ISO utilizada | `ubuntu-24.04.5-live-server-amd64.iso` |
| Memoria asignada | 8192 MB (8 GB) |
| Procesadores virtuales definitivos | **2 vCPU** |
| Disco virtual | `srv-servientrega.vdi`, 50 GB |
| Formato de disco | VDI |
| Adaptador 1 | Intel PRO/1000 MT Desktop, **Adaptador puente**, Realtek Wi-Fi |
| Adaptador 2 | Intel PRO/1000 MT Desktop, **Adaptador solo-anfitrión**, `VirtualBox Host-Only Ethernet Adapter #2` |
| Acceso administrativo | Consola VirtualBox y OpenSSH |

> **Nota sobre CPU:** inicialmente se asignaron cuatro vCPU. Ante un bloqueo repetido del arranque del instalador, se redujeron temporalmente a dos; el instalador avanzó y la instalación se completó con esa configuración. Por tanto, el valor **implementado y validado es 2 vCPU**. La prueba no demuestra de manera concluyente que cuatro vCPU fueran la causa del bloqueo.

## 4. Arquitectura de conectividad

### 4.1. Esquema lógico

```text
                  Internet / red Wi-Fi existente
                              |
                   Red física 192.168.80.0/24
                              |
             Adaptador puente de Oracle VirtualBox
                              |
                  enp0s3 — DHCP — 192.168.80.46/24
                      +-------------------+
                      |  srv-servientrega |
                      | Ubuntu 24.04.5 LTS|
                      +-------------------+
                  enp0s8 — fija — 192.168.10.10/24
                              |
                 VirtualBox Host-only 192.168.10.0/24
                              |
                  Windows anfitrión 192.168.10.1/24
                              |
                Futuros clientes Linux del laboratorio
```

La IP `192.168.80.46` es la asignación DHCP **observada durante las pruebas**, no una dirección permanente garantizada. La IP `192.168.10.10` se configuró estáticamente para el servidor.

### 4.2. Parámetros de red

| Parámetro | Adaptador puente | Adaptador solo-anfitrión |
|---|---|---|
| Interfaz Ubuntu | `enp0s3` | `enp0s8` |
| Función | Salida a red física e Internet | Red privada del laboratorio |
| Modo de VirtualBox | Bridged Adapter | Host-only Adapter |
| IP verificada | `192.168.80.46/24` | `192.168.10.10/24` |
| Asignación | DHCP de la red física | Estática |
| Red | `192.168.80.0/24` | `192.168.10.0/24` |
| Puerta de enlace | `192.168.80.1`, observada | Sin puerta de enlace |
| DNS | Configuración recibida por la red física | Sin DNS específico durante la instalación |

En Windows se identificaron dos interfaces Host-only:

- `Ethernet 2`: `VirtualBox Host-Only Ethernet Adapter`, IP `192.168.56.1`.
- `Ethernet 3`: `VirtualBox Host-Only Ethernet Adapter #2`, IP `192.168.10.1`.

Se seleccionó expresamente **Adapter #2** para la VM. La existencia del adaptador anterior no impidió el funcionamiento y no fue necesario eliminarlo. El DHCP de VirtualBox para la red privada se mantuvo deshabilitado, dado que el direccionamiento del servidor se realiza manualmente.

### 4.3. Reproducción de la configuración de red virtual

Con la VM apagada, en **VirtualBox → Configuración → Red**:

1. **Adaptador 1:** activar; «Conectado a: Adaptador puente»; elegir la interfaz Wi-Fi Realtek del anfitrión; dejar «Cable conectado» activado.
2. **Adaptador 2:** activar; «Conectado a: Adaptador solo-anfitrión»; elegir `VirtualBox Host-Only Ethernet Adapter #2`; dejar «Cable conectado» activado.
3. En el administrador de redes Host-only de VirtualBox, configurar la interfaz seleccionada con IPv4 `192.168.10.1`, máscara `255.255.255.0`, y **deshabilitar el servidor DHCP de VirtualBox**.
4. No agregar una puerta de enlace a la interfaz Host-only del invitado.

La configuración puente depende de las condiciones de la red Wi-Fi utilizada. El direccionamiento Host-only, en cambio, permanece dentro de la red virtual privada del equipo anfitrión.

## 5. Procedimiento de implementación

### 5.1. Verificación de prerrequisitos del anfitrión

1. Abrir `msinfo32` en Windows para revisar sistema operativo, CPU, RAM y modo de firmware.
2. Abrir **Administrador de tareas → Rendimiento → CPU** y comprobar que «Virtualización» figure como habilitada.
3. Comprobar espacio libre en el SSD; se declaró disponibilidad de al menos 100 GB.
4. Confirmar que el equipo dispone de conexión Wi-Fi para el adaptador puente.
5. Revisar si existen adaptadores VirtualBox Host-only previos, para seleccionar el correcto sin eliminar interfaces innecesariamente.

### 5.2. Instalación de Oracle VirtualBox

1. Obtener el instalador de VirtualBox para Windows desde el sitio oficial: <https://www.virtualbox.org/>.
2. Ejecutar el instalador en Windows con los permisos que solicite.
3. Completar el asistente de instalación, aceptando la instalación de los componentes de red de VirtualBox necesarios para los modos puente y solo-anfitrión.
4. Abrir **Oracle VirtualBox Administrador**.
5. Confirmar la versión instalada en **Ayuda → Acerca de VirtualBox**. En esta implementación se verificó **7.2.22 r175245**.
6. Verificar en las propiedades del adaptador Wi-Fi de Windows la presencia del componente **VirtualBox NDIS6 Bridged Networking Driver**.

**Resultado observado:** VirtualBox se instaló y abrió correctamente; el controlador de red puente apareció habilitado en las propiedades de la interfaz Wi-Fi.

### 5.3. Preparación de la red Host-only

1. En VirtualBox, acceder al administrador de redes solo-anfitrión (Host-only Networks), según la ubicación disponible en la versión instalada.
2. Crear o seleccionar la red que se utilizará para Servientrega.
3. Establecer la dirección IPv4 del adaptador anfitrión en `192.168.10.1/24`.
4. Desactivar el servidor DHCP de VirtualBox para esa red.
5. Identificar en Windows el adaptador correspondiente. En este caso fue `VirtualBox Host-Only Ethernet Adapter #2`, alias `Ethernet 3`.
6. Verificar las interfaces desde PowerShell:

```powershell
Get-NetIPConfiguration |
    Where-Object { $_.InterfaceAlias -in @('Ethernet 2','Ethernet 3') } |
    Format-List InterfaceAlias,InterfaceDescription,IPv4Address

Get-NetAdapter |
    Where-Object { $_.Status -eq 'Up' } |
    Format-Table Name,InterfaceDescription,Status,LinkSpeed
```

**Resultado observado:** `Ethernet 3` presentó `192.168.10.1`, y la interfaz Wi-Fi y las interfaces Host-only estaban activas.

### 5.4. Creación de la máquina virtual

1. Seleccionar **Nueva** en Oracle VirtualBox.
2. Asignar el nombre `srv-servientrega`.
3. Seleccionar el tipo de sistema **Ubuntu 24.04 LTS (64-bit)**.
4. Preparar la instalación manual desde la ISO oficial `ubuntu-24.04.5-live-server-amd64.iso`, evitando depender de la imagen auxiliar de instalación desatendida.
5. Asignar **8192 MB de RAM**.
6. Asignar **2 procesadores virtuales** como configuración definitiva verificada.
7. Crear un disco virtual VDI de **50 GB** y asociarlo al controlador SATA.
8. Montar la ISO de Ubuntu Server en la unidad óptica desde **Configuración → Almacenamiento**.
9. En **Sistema → Placa base**, priorizar **Óptica** para el arranque inicial y mantener **Disco duro** habilitado; desactivar Disquete.
10. Configurar los adaptadores de red según el apartado 4.3.
11. Revisar el resumen de la VM antes de iniciarla.

**Precaución:** el disco `srv-servientrega.vdi` es el destino de instalación del invitado. No se debe seleccionar el disco físico de Windows para operaciones de formateo.

### 5.5. Arranque del instalador e incidencia resuelta

Durante los primeros intentos, el arranque se detuvo durante varios minutos en el mensaje:

```text
Begin: Loading essential drivers...
```

Se revisaron el medio de instalación, el orden de arranque y los registros de VirtualBox. El registro contenía una advertencia sobre el modo de ejecución con el hipervisor de Windows:

```text
NEMR3Init: Snail execution mode is active!
```

La advertencia sugiere una posible limitación de rendimiento, **pero no identifica por sí sola la causa del bloqueo**.

**Acción que permitió continuar:** con la VM apagada se modificó **Sistema → Procesador**, reduciendo de cuatro a **dos vCPU**, sin alterar RAM, disco ni red. En el siguiente intento el instalador avanzó hasta sus pantallas interactivas y se completó la instalación.

No fue necesario deshabilitar Hyper-V, VBS, Integridad de memoria ni otras protecciones de Windows. Se conservó la arquitectura de red aprobada.

### 5.6. Instalación de Ubuntu Server 24.04.5 LTS

1. Iniciar `srv-servientrega` y seleccionar **Try or Install Ubuntu Server**.
2. Elegir **inglés** como idioma del instalador, según la configuración utilizada.
3. En **Choose the type of installation**, seleccionar **Ubuntu Server** estándar, no la variante minimized.
4. Mantener desmarcada **Search for third-party drivers**.
5. En **Network configuration**, comprobar que `enp0s3` recibe una dirección por DHCP; se observó `192.168.80.46/24`.
6. Editar IPv4 de `enp0s8`, elegir **Manual** y establecer:

   | Campo | Valor |
   |---|---|
   | Subnet | `192.168.10.0/24` |
   | Address | `192.168.10.10` |
   | Gateway | Vacío |
   | Name servers | Vacío durante la instalación |
   | Search domains | Vacío |

7. Confirmar que ambas interfaces figuren configuradas antes de continuar.
8. En **Proxy configuration**, dejar el campo vacío, ya que no se utilizó un proxy.
9. En **Ubuntu archive mirror configuration**, conservar `http://archive.ubuntu.com/ubuntu/`. El instalador mostró **This mirror location passed tests** y recuperó índices de `noble`, `noble-updates` y `noble-backports`.
10. En **Guided storage configuration**, seleccionar **Use an entire disk**, el disco virtual `VBOX HARDDISK` de 50 GB, **desmarcar LVM** y no habilitar cifrado LUKS.
11. Revisar el resumen de almacenamiento. La propuesta verificada fue:

    | Partición | Tamaño mostrado | Función |
    |---|---:|---|
    | 1 | 1 MB | BIOS GRUB spacer |
    | 2 | 49.997 GB | `ext4`, montada en `/` |

12. Confirmar la escritura de cambios **únicamente en el disco virtual de 50 GB**.
13. Completar **Profile configuration** con el nombre del servidor `srv-servientrega` y el usuario administrativo `adminserv`. La contraseña fue definida localmente y **no se registra en este documento**.
14. En **SSH configuration**, activar **Install OpenSSH server**, conservar habilitada la autenticación por contraseña y no importar claves SSH en esta etapa.
15. No seleccionar aplicaciones opcionales en **Featured Server Snaps**.
16. Esperar a que el instalador termine de copiar el sistema, instalar el kernel, configurar GRUB, instalar OpenSSH y aplicar actualizaciones.
17. Seleccionar **Reboot Now** cuando la instalación finalice. Si el instalador solicita retirar el medio de instalación, desmontar la ISO desde **Dispositivos → Unidades ópticas** y continuar el reinicio.
18. Iniciar sesión en la consola con `adminserv` y su contraseña.

**Resultado observado:** apareció el indicador `Ubuntu 24.04.5 LTS srv-servientrega tty1`; el inicio de sesión fue exitoso.

### 5.7. Verificación del sistema operativo

Desde la consola del servidor:

```bash
hostnamectl
```

Se comprobó:

- Nombre estático: `srv-servientrega`.
- Sistema operativo: Ubuntu 24.04.5 LTS.
- Kernel observado: `6.8.0-149-generic`.
- Arquitectura: `x86-64`.
- Plataforma virtual: Oracle VirtualBox.

En el mensaje de bienvenida se observó que la partición raíz tenía aproximadamente **48.91 GiB**, con un **13.7 % de utilización** en ese momento.

### 5.8. Verificación de interfaces, rutas y conectividad

Ejecutar:

```bash
ip -br addr
ip route
ping -c 4 1.1.1.1
ping -c 4 192.168.10.1
ping -c 4 archive.ubuntu.com
getent ahostsv4 archive.ubuntu.com
```

**Resultados observados:**

| Prueba | Evidencia obtenida | Evaluación |
|---|---|---|
| IP puente | `enp0s3` = `192.168.80.46/24` | Conforme |
| IP privada | `enp0s8` = `192.168.10.10/24` | Conforme |
| Ruta predeterminada | `default via 192.168.80.1 dev enp0s3` | Conforme |
| Ruta privada | `192.168.10.0/24 dev enp0s8` | Conforme |
| Internet por IP | `ping 1.1.1.1`: 4 transmitidos, 4 recibidos, 0 % pérdida | Conforme |
| Windows anfitrión | `ping 192.168.10.1`: 4 transmitidos, 4 recibidos, 0 % pérdida | Conforme |
| DNS externo y conectividad | `ping archive.ubuntu.com`: 4 transmitidos, 4 recibidos, 0 % pérdida | Conforme |
| Resolución IPv4 | `getent ahostsv4 archive.ubuntu.com` devolvió direcciones IPv4 | Conforme |

Estos resultados demuestran conectividad y resolución DNS **externa**. No constituyen una prueba del futuro DNS interno `servientrega.lab`.

### 5.9. Instalación y prueba de OpenSSH

OpenSSH se seleccionó durante la instalación del sistema. Para comprobar su funcionamiento se utilizaron:

```bash
sudo systemctl status ssh --no-pager
sudo ss -lntp | grep ':22 '
```

La salida de `systemctl` mostró inicialmente `ssh.service` como `inactive (dead)` y `TriggeredBy: ssh.socket`. La inspección de sockets mostró el puerto TCP 22 en escucha en IPv4 e IPv6. Esta combinación es compatible con la **activación por socket** de OpenSSH.

La prueba funcional definitiva se efectuó desde **PowerShell de Windows**:

```powershell
ssh adminserv@192.168.10.10
```

En la primera conexión se mostró la huella de la clave del anfitrión SSH; tras aceptar la clave del servidor conocido y proporcionar la contraseña del usuario, apareció el indicador:

```text
adminserv@srv-servientrega:~$
```

**Resultado:** acceso remoto desde Windows confirmado. La administración posterior puede realizarse mediante SSH sin depender de la consola gráfica de VirtualBox.

**Recomendación de seguridad:** en futuras revisiones, considerar autenticación con claves SSH y restringir el acceso al puerto 22 a las redes administrativas autorizadas. La autenticación por contraseña se mantuvo para facilitar la puesta en servicio inicial del entorno aislado de laboratorio.

### 5.10. Mantenimiento inicial de Ubuntu

Se ejecutaron los comandos de actualización:

```bash
sudo apt update
sudo apt upgrade
```

Posteriormente se verificó la necesidad de reinicio:

```bash
if [ -f /var/run/reboot-required ]; then
    echo "REINICIO REQUERIDO"
else
    echo "NO SE REQUIERE REINICIO"
fi
```

**Resultado observado:** `NO SE REQUIERE REINICIO`.

Una comprobación posterior con `sudo apt update` indicó tres paquetes actualizables. Para identificar su situación se utilizó una simulación:

```bash
sudo apt-get -s upgrade
```

La salida indicó que `distro-info`, `python3-distro-info` y `snapd` estaban **diferidos por phased updates**:

```text
0 upgraded, 0 newly installed, 0 to remove and 3 not upgraded.
```

Se optó por **no forzar** esas actualizaciones escalonadas. Su presencia no impidió las verificaciones realizadas. Las versiones disponibles pueden cambiar en comprobaciones futuras.

### 5.11. Configuración de zona horaria y verificación de reloj

Se inspeccionó la configuración inicial y se estableció la zona horaria colombiana:

```bash
timedatectl
sudo timedatectl set-timezone America/Bogota
timedatectl
date
systemctl is-active systemd-timesyncd
```

**Resultados observados:**

- `Time zone: America/Bogota (-05, -0500)`.
- `System clock synchronized: yes`.
- `NTP service: active`.
- `systemd-timesyncd`: `active`.
- El comando `date` mostró la hora local con desplazamiento `-05`.

Esta comprobación corresponde a la **sincronización del propio servidor como cliente de tiempo**; no implica que se haya configurado todavía un servidor NTP para los demás equipos.

## 6. Registro de incidencias y decisiones técnicas

| Incidencia u observación | Diagnóstico o consideración | Acción y resultado |
|---|---|---|
| Tipo de invitado inicialmente configurado como Ubuntu 25.04 | No coincidía con el sistema planificado | Se seleccionó Ubuntu 24.04 LTS (64-bit) |
| ISO inicialmente asociada a Ubuntu 26.04.1 | La versión de la ISO determina qué sistema se instala | Se sustituyó por `ubuntu-24.04.5-live-server-amd64.iso` |
| Unidad óptica asociada inicialmente a ISO auxiliar desatendida | No correspondía al medio normal de instalación manual | Se montó la ISO oficial de Ubuntu Server |
| Dos adaptadores Host-only en Windows | Solo uno pertenecía a la red privada definida | Se conservó y seleccionó Adapter #2 (`192.168.10.1`) |
| Bloqueo en `Loading essential drivers...` | Causa exacta no demostrada; registro con advertencia sobre hipervisor de Windows | Se redujeron los vCPU de 4 a 2; el instalador avanzó |
| Interfaz Host-only sin autoconfiguración DHCP | DHCP deshabilitado intencionalmente | Se configuró IP estática `192.168.10.10/24` |
| `ssh.service` inicialmente inactivo | `ssh.socket` escuchaba en TCP 22 | Se verificó conexión SSH real desde Windows, satisfactoria |
| Tres paquetes pendientes | Actualizaciones escalonadas de Ubuntu | No se forzaron; mantenimiento operativo |

## 7. Matriz de aceptación técnica

| Criterio de funcionamiento | Evidencia | Resultado |
|---|---|---|
| VirtualBox ejecuta la VM | Consola de Ubuntu y sesión SSH operativas | Conforme |
| Ubuntu inicia desde el disco virtual | Pantalla `tty1` e inicio de sesión | Conforme |
| Identidad del sistema | `hostnamectl` | Conforme |
| Interfaz puente con DHCP | `ip -br addr` | Conforme |
| Interfaz Host-only estática | `ip -br addr` | Conforme |
| Enrutamiento de salida por interfaz puente | `ip route` | Conforme |
| Acceso a Internet | `ping 1.1.1.1` | Conforme |
| Comunicación con anfitrión Windows | `ping 192.168.10.1` | Conforme |
| Resolución de dominios externos | `ping` y `getent` | Conforme |
| Puerto SSH disponible | `ss -lntp` | Conforme |
| Autenticación y administración remota | PowerShell `ssh adminserv@192.168.10.10` | Conforme |
| Zona horaria Colombia | `timedatectl` | Conforme |
| Sincronización de reloj del servidor | `timedatectl` y `systemd-timesyncd` | Conforme |
| Reinicio requerido tras mantenimiento | Comprobación de `/var/run/reboot-required` | No requerido en la comprobación |

## 8. Evidencias gráficas recomendadas para el repositorio

Las capturas obtenidas durante la implementación pueden organizarse en una carpeta `capturas/virtualbox-ubuntu/` con nombres descriptivos. Se recomienda conservar, al menos:

1. Características del equipo anfitrión y virtualización habilitada.
2. Versión instalada de Oracle VirtualBox.
3. Resumen de hardware, disco e ISO de `srv-servientrega`.
4. Configuración del adaptador puente y del adaptador Host-only.
5. Direcciones de las interfaces Host-only en Windows.
6. Pantalla de configuración de red del instalador.
7. Validación del mirror oficial de Ubuntu.
8. Resumen de particiones antes de confirmar la instalación.
9. Pantalla de instalación y configuración de OpenSSH.
10. `hostnamectl` tras el primer inicio.
11. `ip -br addr`, `ip route` y pruebas de conectividad.
12. Resolución DNS externa, puerto 22 y acceso SSH desde PowerShell.
13. `timedatectl`, `systemd-timesyncd` y comprobación de actualizaciones.

**Nota:** las capturas son evidencias disponibles en el registro de implementación, pero **no se encuentran incrustadas en este archivo Markdown**. Deben copiarse a la carpeta de evidencias al consolidar el repositorio. No se deben incluir contraseñas ni otros secretos en las imágenes.

## 9. Consideraciones operativas y límites

- La IP del adaptador puente puede variar al cambiar de red Wi-Fi o renovar DHCP. Para administración estable desde el anfitrión se utiliza `192.168.10.10` por Host-only.
- La red Host-only permite comunicación privada entre Windows y las VM conectadas a esa red; no sustituye automáticamente la conectividad entre los equipos físicos de otros integrantes del equipo.
- La dirección `192.168.10.10` debe mantenerse reservada para el servidor dentro de la red privada.
- La VM permanece con **2 vCPU**, configuración con la cual se verificó el arranque. Cualquier aumento posterior de CPU deberá probarse antes de considerarlo definitivo.
- La zona horaria `America/Bogota` controla la presentación de la hora local; la prestación de NTP a clientes es un servicio distinto.
- El DNS externo funciona. El dominio interno `servientrega.lab` y `dnsmasq` todavía no forman parte de este componente.
- No se han instalado Docker, Dokploy ni MySQL como parte de este documento.
- Se recomienda crear una copia de seguridad o una instantánea de VirtualBox del servidor base, preferiblemente con la VM apagada, antes de introducir cambios importantes. **No se afirma que dicha instantánea ya exista**.
- Los controles de acceso y las reglas de firewall deberán revisarse cuando se publiquen servicios adicionales; no se atribuyen a esta instalación políticas de firewall aún no verificadas.

## 10. Conclusión

La sede operativa simulada de Servientrega dispone de un servidor virtual `srv-servientrega` con Ubuntu Server 24.04.5 LTS, recursos de cómputo asignados, almacenamiento local, conectividad puente y privada, administración SSH desde Windows y configuración horaria adecuada para Colombia.

Las pruebas realizadas demostraron el funcionamiento de la plataforma base, la comunicación con el equipo anfitrión, la salida a Internet y la resolución de nombres externos. Esta plataforma proporciona el entorno necesario para incorporar, en documentos técnicos separados, los servicios de administración y operación de infraestructura previstos para la sede.
