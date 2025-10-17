import os
import csv
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv #usar variables de entorno en deployment

# --------------------
# Configuración
# --------------------

load_dotenv("keys.env")

CSV_WHITELIST = "whitelist.csv"

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")


CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError(
    "Faltan CLIENT_ID o CLIENT_SECRET en las variables de entorno. "
    )

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

# SISTEMA DE WHITELIST

def leer_whitelist():
#leemos el csv de la whitelist y retornamos un diccionario con sus valores
    existe_csv(CSV_WHITELIST, ["correo"])
    valores = []
    with open(CSV_WHITELIST, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            v = (row.get("correo") or "").strip() # or "" en caso de que la whitelist tenga valores que podrían ser falsos tipo "None" o "0"
                                                  # strip le saca los espacios antes y después
            if not v: #checkeamos si v es "", y si es lo salteamos
                continue
            valores.append(v)
    return valores


def esta_permitido(email):
    whitelist = leer_whitelist()
    #si la whitelist está vacía permitimos todos los usuarios
    if not whitelist:
        return True, "no hay whitelist configurada, se permiten todos los usuarios"

    #reviso si hay coincidencia exacta
    for item in whitelist:
        if email.lower() == item.lower():
            return True, f"coincidencia: {item}"

    return False, "no está en la whitelist"

# HISTORIAL DE LOGEO DE USUARIOS

def guardar_login_usuario(email):
 #guarda la fecha y hora del login en un archivo CSV individual en de la carpeta login_data.
    
    carpeta = "login_data"
    os.makedirs(carpeta, exist_ok=True)  # crea la carpeta si no existe
    permitido = esta_permitido(email)
    
    # me quedo con lo que está antes del .
    nombre_archivo = email.partition(".")[0] + ".csv" 
    ruta_archivo = os.path.join(carpeta, nombre_archivo)

    # Si el archivo no existe, lo creamos con encabezado y luego agregamos la fila con el last_login
    # y un campo que nos diga si el usuario está permitido o no en el sistema
    existe_csv(ruta_archivo,["last_login", "allowed"])
    with open(ruta_archivo, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), permitido[0]])


# -----------------------
# Rutas de la página web
# -----------------------

@app.route("/")
def index():
    #verificamos si hay una sesión buscando el correo, si hay mostramos cerrar sesión y si no iniciarla
    #si el correo existe verificamos que esté en la whitelist
    user_email = session.get("email")
    
    if user_email:
        permitido = esta_permitido(user_email)
        if permitido[0]:
            username = session.get("nombre")
            return f"¡Hola {username}! ¡Tu correo ({user_email}) está permitido! <a href='/logout'>Cerrar sesión</a>"
            #return render_template("index.html", email=user_email, username=username)
        else:
            return f"¡Hola {user_email}! Tu correo ({user_email}) NO está permitido en esta página, por favor cierra sesión. <a href='/logout'>Cerrar sesión</a>"
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
    google.authorize_access_token() #no me guardo el token porque no lo necesito
    userinfo_endpoint = google.server_metadata['userinfo_endpoint']
    res = google.get(userinfo_endpoint)
    info_usuario = res.json()
    # me guardo correo, nombre e imagen del usuario
    email = info_usuario['email']
    nombre = info_usuario['name']
    foto = info_usuario['picture']
    
    # agregamos fecha nueva de logeo para el usuario
    guardar_login_usuario(email)

    # guardamos el correo, nombre y foto en la sesión de flask, que dura hasta que se cierre el navegador
    session["email"] = email
    session["nombre"] = nombre
    session["foto"] = foto

    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    #cerramos sesión y volvemos al inicio
    session.clear()
    return redirect(url_for("index"))


@app.route("/debug")
def debug():
    #esta ruta está para printear cosas del desarrollo, solo de prueba
    whitelist = leer_whitelist()
    return f"<pre>{whitelist}</pre>"


if __name__ in "__main__":
    app.run(debug=True)