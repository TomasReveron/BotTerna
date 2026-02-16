import json
import os
from time import strftime


def cargar_materias():
    materias_path = os.path.join(os.path.dirname(__file__), "materias.json")
    if not os.path.isfile(materias_path):
        raise SystemExit("No se encontro materias.json en el proyecto.")

    with open(materias_path, "r", encoding="utf-8") as materias_file:
        data = json.load(materias_file)

    if not isinstance(data, dict) or not data:
        raise SystemExit("materias.json debe contener un objeto con materias y secciones.")

    normalizado = {}
    for nombre, valor in data.items():
        if isinstance(valor, list):
            normalizado[nombre] = {"secciones": valor, "inscrita": False}
            continue

        if not isinstance(valor, dict):
            raise SystemExit("Cada materia debe ser una lista o un objeto con secciones.")

        secciones = valor.get("secciones")
        if not isinstance(secciones, list) or not secciones:
            raise SystemExit("Cada materia debe tener una lista de secciones.")

        inscrita = bool(valor.get("inscrita", False))
        normalizado[nombre] = {"secciones": secciones, "inscrita": inscrita}

    return normalizado


def guardar_materias(materias):
    materias_path = os.path.join(os.path.dirname(__file__), "materias.json")
    with open(materias_path, "w", encoding="utf-8") as materias_file:
        json.dump(materias, materias_file, ensure_ascii=False, indent=2)


def materias_pendientes(materias):
    return [nombre for nombre, info in materias.items() if not info.get("inscrita")]


def construir_estado(materias, intentos):
    pendientes = materias_pendientes(materias)
    lineas = [
        (
            f"Estado: activo | Intentos: {intentos} | Pendientes: {len(pendientes)} | "
            f"Hora: {strftime('%Y-%m-%d %H:%M:%S')}"
        ),
        "Materias:"
    ]

    for nombre, info in materias.items():
        estado = "inscrita" if info.get("inscrita") else "no inscrita"
        lineas.append(f"- {nombre}: {estado}")

    return "\n".join(lineas)
