import os
import csv
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from authlib.integrations.flask_client import OAuth
from authlib.integrations.base_client import OAuthError
from dotenv import load_dotenv #usar variables de entorno en deployment

# --------------------
# Configuración
# --------------------

load_dotenv("keys.env")

CSV_WHITELIST = "whitelist.csv"

app = Flask(__name__)

SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Falta FLASK_SECREY_KEY en las variables de entorno")
app.secret_key = SECRET_KEY


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


# --------------------------------------------------------------------
# Funcion para revisar si el usuario está usando un dispositivo móvil
# --------------------------------------------------------------------

def is_mobile():
    #me fijo si el user_agent de flask registra algo que contenga ciertos strings que
    #indicarían si es un dispositivo móvil
    user_agent = request.user_agent.string.lower()
    palabras_clave = [
        "iphone", "android", "ipad", "mobile", "windows phone",
        "opera mini", "blackberry", "iemobile"
    ]
    return any(valor in user_agent for valor in palabras_clave)

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
    nombre_archivo = "clusters_" + email.replace("@","_").replace(".","_") + ".csv" 
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
    
    # para esto el método más seguro y escalable (supuestamente) es usar un csv temporal
    # que al final se lo sobreescribimos al original, entonces abrimos los dos archivos
    # simultáneamente, leemos del original y escribimos en el temporal
    # una vez hayamos sustituído lo que queríamos y el csv temporal esté completo,
    # le cambiamos el nombre al temporal por el del archivo original, quedando así
    # un único archivo con el cambio realizado
    
    carpeta = "user_output/tagged/clusters"
    os.makedirs(carpeta, exist_ok=True)
    nombre_archivo = "clusters_" + email.replace("@","_").replace(".","_") + ".csv" 
    temp_file = "clusters_" + email.replace("@","_").replace(".","_") + "_tmp.csv"
    ruta_archivo = os.path.join(carpeta, nombre_archivo)
    ruta_archivo_tmp = os.path.join(carpeta, temp_file)
    

    with open(ruta_archivo, newline="", encoding="utf-8") as f_in, \
        open(ruta_archivo_tmp, "w", newline="", encoding="utf-8") as f_out:
    
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames) # copio las cabeceras del original
        writer.writeheader() # escribo las cabeceras
    
        for row in reader:
            if row["image"] == nombre:     
                row["is_tagged"] = True 
            writer.writerow(row)

    os.replace(ruta_archivo_tmp, ruta_archivo) 


def obtener_lista_cluster_csv(email):
    # de ese csv obtener una lista que tenga solo aquellas imágenes cuyo campo is_tagged sea False
    # aleatorizar la lista y devolverla 
    
    carpeta = "user_output/tagged/clusters"
    os.makedirs(carpeta, exist_ok=True)
    nombre_archivo = "clusters_" + email.replace("@","_").replace(".","_") + ".csv" 
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

# OUTPUT CSV

def agregar_etiquetas_output_csv(email, nombre_imagen, etiquetas):
    # esta función recibe el nombre de un grupo de imágenes, una lista de etiquetas
    # ordenadas (0-15), y el correo del usuario
    # crea un csv con el mail del usuario que corresponde a los datos finales
    # dos columnas: image y tag
    #
    
    carpeta = "user_output/tagged/images"
    os.makedirs(carpeta, exist_ok=True)
    nombre_archivo = "tags_" + email.replace("@","_").replace(".","_") + ".csv" 
    ruta_archivo = os.path.join(carpeta, nombre_archivo)
    existe_csv(ruta_archivo,["image", "tag"])
    
    with open(ruta_archivo, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for idx, etiqueta in enumerate(etiquetas):
            imagen = f"{nombre_imagen}_{idx}"
            writer.writerow([imagen, etiqueta])
    

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
    nombre_archivo = "login_" + email.replace("@","_").replace(".","_") + ".csv" 
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
    #reviso si está en un dispositivo móvil
    
    if is_mobile():
        return "<h1>No está permitido utilizar la página desde dispositivos móviles.</h1>"
    
    #manejo la lógica del inicio de sesión adentro del template
    user_email = session.get("email")
    username = session.get("nombre")
    permitido = None

    if user_email:
        permitido = esta_permitido(user_email)[0]
        
    if permitido:
        inicializar_cluster_csv(user_email)

    return render_template("Registro_win.html", email=user_email, username=username, permitido=permitido)
    

@app.route('/etiquetado')
def etiquetado():
    # acá vamos a usar la sesión de flask para manejar la lista aleatorizada
    # revisamos si ya hay una lista guardada en la sesión, si no hay la obtenemos y
    # la guardamos en la sesión, esta después la cargamos en enviar_etiquetas y la vamos
    # popeando a medida que se envían las etiquetas
    # si ya hay una lista guardada entonces directamente la cargamos de ahí.
    # como vamos a ir popeando la lista, leemos siempre el primer elemento.
    
    if is_mobile():
        return "<h1>No está permitido utilizar la página desde dispositivos móviles.</h1>"
    
    email = session.get("email")
    
    # acá reviso si el usuario trató de entrar a la página poniendo /etiquetado en la URL directamente
    # o sea que si no hay mail en la sesión o no está permitido lo vuelvo a mandar a la página principal
    if not email:
        return redirect(url_for("index"))
    if not esta_permitido(email)[0]:
        return redirect(url_for("index"))
    
    if "imagenes_aleatorizadas" not in session:
        imagenes = obtener_lista_cluster_csv(email)
        session["imagenes_aleatorizadas"] = imagenes

    imagenes = session.get("imagenes_aleatorizadas")
    
    if not imagenes:
        return render_template("NoMoreImages.html")
    
    imagen_actual = imagenes[0]
    restantes = len(imagenes)
    
    return render_template('Etiquetador_win.html', imagen=imagen_actual, restantes=restantes)


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
    
    # reviso si el usuario canceló el login
    error = request.args.get("error")
    if error:
        app.logger.warning(f"Falló o se canceló el inicio de sesión con Google: {error}")
        flash("No autorizaste el acceso con Google.", "error")
        return redirect(url_for("index"))

    # uso un try para revisar si hubo algún error por parte de google al iniciar sesión
    try:
        google.authorize_access_token()  # no me guardo el token porque no lo necesito
    except OAuthError as e:
        app.logger.error(f"Error obteniendo token de acceso: {str(e)}")
        flash("Hubo un problema con el inicio de sesión de Google.", "error")
        return redirect(url_for("index"))
    
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


@app.route("/enviar_etiquetas", methods=["POST"])
def enviar_etiquetas():
    # recupero una lista ordenada de 16 elementos del javascript
    # correspondiente a Etiquetador_win.html usando el request de flask
    # si la lista está vacía tiro un error
    # acá me guardo la primera imagen de la lista de imágenes y le hago un pop a la lista para borrar
    # el elemento.
    # esa nueva lista sin el primer elemento me la guardo de nuevo en la sesión
    # uso las funciones que definí para
    # 1. guardar las etiquetas de las 16 sub-imágenes
    # 2. marcar el grupo de imágenes como etiquetado
    email = session.get("email")
    imagenes = session.get("imagenes_aleatorizadas", [])
    
    if not imagenes:
        return {"error": "No quedan imágenes"}, 400
    
    imagen_actual = imagenes.pop(0)
    session["imagenes_aleatorizadas"] = imagenes
    
    etiquetas = request.get_json()
    # procesar y guardar

    agregar_etiquetas_output_csv(email, imagen_actual, etiquetas)
    actualizar_elemento_cluster_csv(email, imagen_actual)
    
    
    
    # confirmación
    return jsonify({"status": "ok"})


if __name__ in "__main__":
    app.run(debug=True)