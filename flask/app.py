import os
import csv
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from authlib.integrations.flask_client import OAuth
from api_key import * #usar variables de entorno en deployment

# --------------------
# Configuración
# --------------------

CSV_USUARIOS = "usuarios.csv"

app = Flask(__name__)
app.secret_key = "7Abcet3dsd2F.sfw-Gwa2" #meter esto en las variables de entorno

oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope':'openid profile email'}
)




# ----------------------------------------
# Funciones auxiliares para manejo de CSVs
# ----------------------------------------
def existe_csv(ruta, cabeceras):
#Crea un CSV con cabecera si no existe
    if not os.path.exists(ruta):
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(cabeceras)


def actualizar_usuario(ruta_csv, info_usuario):
#actualiza o inserta una fila nueva en usuarios.csv

    existe_csv(ruta_csv, ["email", "ultimo_login"])
    # cargo las filas de "usuarios.csv" en el diccionario "filas"
    filas = []
    actualizado = False
    with open(ruta_csv, "r", newline="", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        for fila in lector:
            filas.append(fila)

    fecha = datetime.now().isoformat()
    for fila in filas:
        if fila.get("email", "") == info_usuario.get("email"):
            # si el mail ya está en el csv, actualizo la fecha del ultimo logeo
            fila["ultimo_login"] = fecha
            actualizado = True
            break

    if not actualizado:
        # si el mail no estaba, agrego el usuario nuevo
        filas.append({
        "email": info_usuario.get("email", ""),
        "ultimo_login": fecha,
        })

# sobreescribimos el csv con el diccionario "filas" nuevo
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        cabeceras = ["email", "ultimo_login"]
        writer = csv.DictWriter(f, fieldnames=cabeceras)
        writer.writeheader()
        for fila in filas:
            writer.writerow(fila)

# -----------------------
# Rutas de la página web
# -----------------------

@app.route("/")
def index():
    #verificamos si hay una sesión buscando el correo, si hay mostramos cerrar sesión y si no iniciarla
    user_email = session.get("email")
    if user_email:
        return f"Hola {user_email}! <a href='/logout'>Cerrar sesión</a>"
    return "<a href='/login/google'>Iniciar sesión con Google</a>"



@app.route('/login/google')
def login_google():
    try:
        redirect_uri = url_for('authorize_google',_external=True)
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        app.logger.error(f"Error durante el inicio de sesión:{str(e)}")
        return "Ocurrió un error durante el inicio de sesión", 500

@app.route("/authorize/google")
def authorize_google():
    token = google.authorize_access_token()
    session["token"] = token #me guardo el token de google en la sesión de flask
    userinfo_endpoint = google.server_metadata['userinfo_endpoint']
    res = google.get(userinfo_endpoint)
    info_usuario = res.json()
    email = info_usuario['email']
    
    # guardamos al usuario o actualizamos su fecha
    actualizar_usuario(CSV_USUARIOS, {"email": email})

    # guardamos el correo en la sesión
    session["email"] = email

    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    #cerramos sesión y volvemos al inicio
    session.clear()
    return redirect(url_for("index"))


@app.route("/debug")
def debug():
    #esta ruta está para printear cosas del desarrollo, solo de prueba
    print(session)  
    return f"<pre>{json.dumps(dict(session), indent=2)}</pre>"


if __name__ in "__main__":
    app.run(debug=True)