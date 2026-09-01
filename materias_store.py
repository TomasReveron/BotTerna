import json
import os
from time import strftime
from config import obtener_ruta_base


def cargar_materias():
    materias_path = os.path.join(obtener_ruta_base(estatico=False), "materias.json")
    if not os.path.isfile(materias_path):
        # Si no existe, crear una estructura base por defecto
        base_materias = {}
        guardar_materias(base_materias)
        return base_materias

    with open(materias_path, "r", encoding="utf-8") as materias_file:
        try:
            data = json.load(materias_file)
        except Exception:
            data = {}

    if not isinstance(data, dict):
        return {}

    normalizado = {}
    for nombre, valor in data.items():
        if isinstance(valor, list):
            normalizado[nombre] = {"secciones": valor, "inscrita": False}
            continue

        if not isinstance(valor, dict):
            continue

        secciones = valor.get("secciones", [])
        if not isinstance(secciones, list):
            secciones = []

        inscrita = bool(valor.get("inscrita", False))
        normalizado[nombre] = {"secciones": secciones, "inscrita": inscrita}

    return normalizado


def guardar_materias(materias):
    materias_path = os.path.join(obtener_ruta_base(estatico=False), "materias.json")
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
