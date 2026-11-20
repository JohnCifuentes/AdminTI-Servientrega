# Infraestructura de TI para una sede simulada de Servientrega S. A.

**Proyecto final — Administración de Infraestructura de TI**  
**Universidad del Quindío · Facultad de Ingeniería de Sistemas y Computación**  
**Fecha de consolidación:** noviembre de 2026

## Equipo de trabajo

- **John Alexander Cifuentes Murillo**
- **Lida Marcela Gualtero**
- **Liseth Garcia Peña**
- **Juan Pablo Mora**

## Presentación

Este repositorio documenta el diseño, la implementación y la validación de una **infraestructura tecnológica de laboratorio** para una sede operativa *simulada* de Servientrega S. A., con un escenario de nueve personas. No describe sistemas reales de la compañía ni utiliza información corporativa o de clientes.

El objetivo es demostrar cómo una sede puede disponer de servicios compartidos —archivos, impresión, cuentas Linux, hora de red, resolución de nombres y un portal institucional— administrados desde un servidor central. El énfasis del proyecto es la **administración de infraestructura**, no el desarrollo de una aplicación logística.

## Necesidad y solución

Una sede con equipos Windows y Linux necesita intercambiar archivos, compartir una impresora, mantener una referencia horaria, gestionar usuarios de prueba y acceder a información institucional sin configurar cada recurso de manera aislada. Para atender esas necesidades se montó un laboratorio en **Oracle VirtualBox** con **Ubuntu Server**, una red privada de pruebas, servicios Linux tradicionales, **Docker/Dokploy**, **MySQL** y un portal sencillo desarrollado en **Flask**.

## Arquitectura implementada

| Componente | Función y resultado |
|---|---|
| Windows 11 anfitrión | Equipo de administración y cliente de pruebas; `192.168.10.1` en Host-only. |
| `srv-servientrega` | Ubuntu Server 24.04.5 LTS, 2 vCPU, 8 GB RAM y disco virtual de 50 GB; IP interna fija `192.168.10.10`. |
| `client-nfs` | Cliente Ubuntu de pruebas; IP interna `192.168.10.20`. |
| Red de laboratorio | VirtualBox Host-only `192.168.10.0/24`; el servidor también dispone de interfaz puente para conectividad externa. |
| Docker / Docker Swarm / Dokploy | Plataforma de contenedores instalada y validada; Dokploy administra MySQL. |
| DNS (`dnsmasq`) | Resolución de nombres internos bajo `servientrega.lab`. |
| NTP (`Chrony`) | Servicio de referencia horaria para la red privada. |
| NFS | Carpetas Linux compartidas; montajes y transferencia remota comprobados. |
| NIS | Cuentas ficticias Linux centralizadas; autenticación verificada desde Ubuntu cliente. |
| CUPS | Impresora PDF virtual compartida; impresión remota y archivo PDF generado. |
| Samba | Carpeta compartida con acceso y escritura desde Windows. |
| MySQL 8.4 | Base `servientrega_db`, desplegada desde Dokploy, con acceso interno desde Flask. |
| Flask / Gunicorn | Portal con perfiles de demostración **Administrador** y **Operador** y mensajes obtenidos de MySQL. |

La aplicación integrada está disponible **en el laboratorio** mediante `http://192.168.10.10:5001/`. El contenedor inicial de demostración usa `http://192.168.10.10:5000/`; el panel Dokploy usa `http://192.168.10.10:3000/`. Estas direcciones son **privadas**, no enlaces públicos de Internet.

## Organización del repositorio

```text
AdminTI/
├── README.md
├── analisis.md
├── diagrama.mmd
├── infraestructura/
│   ├── 01-virtualbox-ubuntu-server.md
│   ├── 02-docker-dokploy.md
│   ├── 03-servicio-dns-dnsmasq.md
│   ├── 04-servicio-ntp-chrony.md
│   ├── 05-servicio-nfs.md
│   ├── 06-servicio-nis.md
│   ├── 07-servicio-cups.md
│   ├── 08-servicio-samba.md
│   ├── 09-servicio-mysql.md
│   └── 10-portal-web-flask.md
├── codigo/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .dockerignore
│   ├── .env.example
│   ├── templates/index.html
│   └── static/css/styles.css
└── capturas/
    └── [evidencias numeradas del laboratorio]
```

**Guía de lectura:** comenzar por [`analisis.md`](analisis.md) para conocer necesidades, requisitos y resultados; consultar [`diagrama.mmd`](diagrama.mmd) para la topología; revisar cada documento de [`infraestructura/`](infraestructura/) para comandos, configuración y pruebas; y usar [`codigo/`](codigo/) para examinar la aplicación. Las evidencias se relacionan en la sección 14 de `analisis.md`.

## Evidencias y validaciones

Se registraron pruebas de conectividad, administración remota, estado de Dokploy, resolución DNS, sincronización horaria, montajes NFS, inicio de sesión NIS, impresión CUPS, lectura y escritura Samba, consultas MySQL y navegación del portal desde Windows. El inventario entregado por el equipo contiene **32 nombres de capturas** (`00` a `32`, sin `07`). Debe comprobarse que los archivos de imagen correspondientes estén efectivamente guardados en `capturas/` y que las referencias coincidan con sus extensiones.

Las validaciones descritas corresponden al laboratorio y no equivalen a pruebas de carga, seguridad integral o disponibilidad permanente.

## Ejecución del portal web

El código entregado en `codigo/` corresponde a la aplicación Flask documentada. Para ejecutarla se requiere una instancia MySQL accesible desde la red del contenedor, con la base y tabla configuradas como se explica en [`09-servicio-mysql.md`](infraestructura/09-servicio-mysql.md).

1. Copiar `codigo/.env.example` a un archivo local `codigo/.env` y completar la contraseña de laboratorio. **No publicar `.env` ni credenciales**.
2. Construir la imagen desde `codigo/`:

   ```bash
   docker build -t portal-servientrega:2.0 .
   ```

3. En el servidor de laboratorio, con la red `dokploy-network` y el servicio MySQL disponibles, iniciar el contenedor:

   ```bash
   docker run -d \
     --name portal-servientrega-test \
     --network dokploy-network \
     --env-file .env \
     --publish 192.168.10.10:5001:5000 \
     portal-servientrega:2.0
   ```

4. Desde un cliente conectado a la red Host-only, abrir `http://192.168.10.10:5001/`. También pueden comprobarse las rutas `/health` y `/health/db`.

**Nota:** los comandos reproducen la configuración del laboratorio; el nombre del contenedor, la red y los puertos deben estar libres. El repositorio no incluye el contenido del volumen de MySQL ni credenciales reales. El archivo HTML/CSS de la carpeta `codigo/` fue reconstruido a partir de la documentación y puede diferir visualmente de las capturas originales.

## Alcance, seguridad y pendientes

La solución demuestra integración funcional, pero **no debe presentarse como un sistema listo para producción**:

- **HTTPS/TLS no fue configurado.** El portal y Dokploy se validaron mediante HTTP privado.
- **El portal Flask no se desplegó como aplicación administrada por Dokploy**; se ejecutó mediante Docker CLI. **MySQL sí se desplegó en Dokploy**.
- El portal usa dos perfiles de presentación, seleccionables desde la interfaz; **no realiza autenticación ni autorización real**.
- NIS es un protocolo heredado, usado únicamente con identidades ficticias en el laboratorio.
- No se documentó una prueba de restauración de base de datos, una prueba de carga con nueve usuarios simultáneos ni una auditoría integral de seguridad.
- La guía académica menciona servidor web Nginx/Apache y HTTPS; la implementación final usa Flask/Gunicorn sobre HTTP. Esta diferencia debe declararse y contrastarse con la rúbrica.

La trazabilidad detallada de requisitos completos, parciales y pendientes está en [`analisis.md`](analisis.md). No se atribuye a Servientrega S. A. la aprobación ni el uso real de esta infraestructura.

## Presentación del proyecto

La guía académica solicita una exposición de **15 minutos**, con demostración funcional, decisiones de diseño y análisis de costo-beneficio. El equipo dispone de un guion de exposición separado, organizado en cuatro intervenciones y orientado a una audiencia directiva no técnica.

## Referencia académica

*Proyecto Final: Administración de Infraestructura de TI*. Universidad del Quindío, guía de la asignatura proporcionada para la actividad.
