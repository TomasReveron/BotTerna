import os


def cargar_env_local():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.isfile(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            os.environ.setdefault(key, value)


def validar_env():
    faltantes = []

    if not (os.getenv("URL_LOGIN") or os.getenv("URL_UNI")):
        faltantes.append("URL_LOGIN/URL_UNI")
    if not os.getenv("URL_INSCRIPCION"):
        faltantes.append("URL_INSCRIPCION")
    if not os.getenv("USER_UNI"):
        faltantes.append("USER_UNI")
    if not os.getenv("PASS_UNI"):
        faltantes.append("PASS_UNI")

    if faltantes:
        print("⚠️  Faltan variables en el .env: " + ", ".join(faltantes))
        raise SystemExit("No se puede continuar sin estas variables.")


def validar_chromedriver(driver_path):
    if not driver_path:
        # Modo automático: undetected-chromedriver gestionará el driver
        return

    driver_path_abs = os.path.abspath(driver_path)
    if not os.path.isfile(driver_path_abs):
        raise SystemExit(f"Chromedriver no encontrado en: {driver_path}")

    if os.name == "nt":
        if not driver_path.lower().endswith(".exe"):
            raise SystemExit("En Windows, CHROMEDRIVER_PATH debe terminar en .exe")
    else:
        if not os.access(driver_path_abs, os.X_OK):
            raise SystemExit(f"Chromedriver no es ejecutable: {driver_path}")


def obtener_ruta_perfil_chrome():
    perfil_relativo = os.getenv("CHROME_USER_DATA_DIR", "./chrome_profile")
    perfil_abs = os.path.abspath(os.path.join(os.path.dirname(__file__), perfil_relativo))
    os.makedirs(perfil_abs, exist_ok=True)
    return perfil_abs
