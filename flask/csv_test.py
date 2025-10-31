import csv
import os

# campos = ['nombre','edad','dni']
# filas = [
#     ['Nombre1', '24', '42926969'],
#     ['Nombre2', '24', '29383523'],
#     ['Nombre3', '25', '42555838'],
#     ['Nombre4', '32', '43775386']
# ]

# nombre_carpeta = 'CSVs'

# os.makedirs(nombre_carpeta, exist_ok=True)

# nombre_archivo = os.path.join(nombre_carpeta, "lista_personas.csv")

# with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as csvfile:
#     csvwriter = csv.writer(csvfile)
#     csvwriter.writerow(campos)
#     csvwriter.writerows(filas)


imagenes = os.listdir("static/images")
print(len(imagenes))
imagenes.sort()
img = []
for imagen in imagenes:
    idx = imagen.find("_")
    idx2 = imagen.find("_",idx+1)
    ultimo = img[-1] if img else None
    if ultimo != imagen[:idx2]:
        img.append(imagen[:idx2])
print(len(img))
    
    
# def actualizar_usuario(ruta_csv, info_usuario):
# #actualiza o inserta una fila nueva en usuarios.csv

#     existe_csv(ruta_csv, ["email", "ultimo_login"])
#     # cargo las filas de "usuarios.csv" en el diccionario "filas"
#     filas = []
#     actualizado = False
#     with open(ruta_csv, "r", newline="", encoding="utf-8") as f:
#         lector = csv.DictReader(f)
#         for fila in lector:
#             filas.append(fila)

#     fecha = datetime.now().isoformat()
#     for fila in filas:
#         if fila.get("email", "") == info_usuario.get("email"):
#             # si el mail ya está en el csv, actualizo la fecha del ultimo logeo
#             fila["ultimo_login"] = fecha
#             actualizado = True
#             break

#     if not actualizado:
#         # si el mail no estaba, agrego el usuario nuevo
#         filas.append({
#         "email": info_usuario.get("email", ""),
#         "ultimo_login": fecha,
#         })

# # sobreescribimos el csv con el diccionario "filas" nuevo
#     with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
#         cabeceras = ["email", "ultimo_login"]
#         writer = csv.DictWriter(f, fieldnames=cabeceras)
#         writer.writeheader()
#         for fila in filas:
#             writer.writerow(fila)