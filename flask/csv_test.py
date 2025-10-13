import csv
import os

campos = ['nombre','edad','dni']
filas = [
    ['Nombre1', '24', '42926969'],
    ['Nombre2', '24', '29383523'],
    ['Nombre3', '25', '42555838'],
    ['Nombre4', '32', '43775386']
]

nombre_carpeta = 'CSVs'

os.makedirs(nombre_carpeta, exist_ok=True)

nombre_archivo = os.path.join(nombre_carpeta, "lista_personas.csv")

with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(campos)
    csvwriter.writerows(filas)