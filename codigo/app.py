"""Portal institucional de demostración de Servientrega S.A. (laboratorio)."""
import os
import pymysql
from flask import Flask, render_template, request

app = Flask(__name__)


def obtener_perfil(codigo):
    """Consultar un perfil activo; no constituye autenticación de usuarios."""
    conexion = pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        charset="utf8mb4",
        connect_timeout=5,
        read_timeout=5,
        write_timeout=5,
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """SELECT codigo, nombre, mensaje
                   FROM perfiles WHERE codigo = %s AND activo = 1 LIMIT 1""",
                (codigo,),
            )
            return cursor.fetchone()
    finally:
        conexion.close()


@app.route("/", methods=["GET"])
def inicio():
    rol_actual = request.args.get("rol", "operador").strip().lower()
    if rol_actual not in ("administrador", "operador"):
        rol_actual = "operador"
    try:
        rol = obtener_perfil(rol_actual)
    except (pymysql.MySQLError, OSError, KeyError, ValueError):
        app.logger.exception("No fue posible consultar el perfil en MySQL")
        return "Servicio temporalmente no disponible.", 503
    if rol is None:
        return "Perfil no disponible.", 404
    return render_template("index.html", rol_actual=rol_actual, rol=rol)


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "service": "portal-servientrega"}, 200


@app.route("/health/db", methods=["GET"])
def health_db():
    try:
        conexion = pymysql.connect(
            host=os.environ["DB_HOST"],
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
            charset="utf8mb4",
            connect_timeout=5,
            read_timeout=5,
            write_timeout=5,
        )
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        finally:
            conexion.close()
        return {"status": "ok", "database": "connected"}, 200
    except (pymysql.MySQLError, OSError, KeyError, ValueError):
        app.logger.exception("Error en la comprobacion de MySQL")
        return {"status": "error", "database": "unavailable"}, 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
