import os
import csv
import json
import random
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
    existe = True
    if not os.path.exists(ruta):
        existe = False
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(cabeceras)
    return existe


# CLUSTER HANDLING

def inicializar_cluster_csv(email):
    # leer los archivos de static/images y hacer una lista que no tenga las sub-imágenes
    # guardar esa lista en un csv con columnas [image, is_tagged]
    # (los is_tagged siempre estarían en False)
    
    # acá tendría que revisar si el csv ya existe, si lo hace entonces
    # en vez de crear el csv de cero: 
    # - leer toda la columna image del csv
    # - eliminar la intersección de ambas listas 
    # - agregar al final del csv la lista resultante, que debería tener las imagenes agregadas nuevas
    
    carpeta = "user_output/tagged/clusters"
    os.makedirs(carpeta, exist_ok=True)
    nombre_archivo = email.partition(".")[0] + ".csv" 
    ruta_archivo = os.path.join(carpeta, nombre_archivo)
    existe = existe_csv(ruta_archivo,["image", "is_tagged"])
    
    sub_imagenes = os.listdir("static/images")
    sub_imagenes.sort()
    imagenes = []
    for imagen in sub_imagenes:
        idx = imagen.find("_")
        idx2 = imagen.find("_",idx+1)
        ultimo = imagenes[-1] if imagenes else None
        if ultimo != imagen[:idx2]:
            imagenes.append(imagen[:idx2])
    
    if not existe:
        with open(ruta_archivo, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for imagen in imagenes:
                writer.writerow([imagen, False])
    else:
        imagenes_csv = []
        with open(ruta_archivo, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                imagenes_csv.append(row["image"])
        # usamos conjuntos para sacar la intersección de las listas
        dif_simetrica = list(set(imagenes) ^ set(imagenes_csv))
        dif_simetrica.sort()
        with open(ruta_archivo, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for imagen in dif_simetrica:
                writer.writerow([imagen, False])
    

def actualizar_elemento_cluster_csv(email, nombre):
    # recibe el nombre de un elemento del csv
    # lo busca en el csv y le cambia el is_tagged de false a true
    return True

def obtener_lista_cluster_csv(email):
    # de ese csv obtener una lista que tenga solo aquellas imágenes cuyo campo is_tagged sea False
    # aleatorizar la lista y devolverla 
    
    carpeta = "user_output/tagged/clusters"
    os.makedirs(carpeta, exist_ok=True)
    nombre_archivo = email.partition(".")[0] + ".csv" 
    ruta_archivo = os.path.join(carpeta, nombre_archivo)
    
    imagenes_csv = []
    with open(ruta_archivo, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            is_tagged = row["is_tagged"].strip().lower() == "true" #convierto el string en booleano
            if not is_tagged:
                imagenes_csv.append(row["image"])
    random.shuffle(imagenes_csv)

    return imagenes_csv



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
    
    carpeta = "user_output/login_data"
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
    #manejo la lógica del inicio de sesión adentro del template
    user_email = session.get("email")
    username = session.get("nombre")
    permitido = None

    if user_email:
        permitido = esta_permitido(user_email)[0]
        
    if permitido:
        inicializar_cluster_csv(user_email)

    return render_template("Registro_win.html", email=user_email, username=username, permitido=permitido)
    
    
    
    
    
    #verificamos si hay una sesión buscando el correo, si hay mostramos cerrar sesión y si no iniciarla
    #si el correo existe verificamos que esté en la whitelist
    # user_email = session.get("email")
    
    # if user_email:
    #     permitido = esta_permitido(user_email)
    #     if permitido[0]:
    #         username = session.get("nombre")
    #         return f"¡Hola {username}! ¡Tu correo ({user_email}) está permitido! <a href='/logout'>Cerrar sesión</a>"
    #         #return render_template("index.html", email=user_email, username=username)
    #     else:
    #         return f"¡Hola {user_email}! Tu correo ({user_email}) NO está permitido en esta página, por favor cierra sesión. <a href='/logout'>Cerrar sesión</a>"
    # return render_template("Registro_win.html")

#"<a href='/login/google'>Iniciar sesión con Google</a>"

@app.route('/etiquetado')
def etiquetado():
    
    return render_template('Etiquetador_win.html')


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
    email = session.get("email")
    imagenes = obtener_lista_cluster_csv(email)
    return f"<pre>{imagenes}</pre>"


if __name__ in "__main__":
    app.run(debug=True)