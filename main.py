from time import sleep, strftime
from threading import Event, Lock, Thread
import os
import json
import urllib.parse
import urllib.request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def iniciar_bot():
    # 1. Definir la ruta absoluta
    # Asegúrate de que el nombre sea exactamente 'chromedriver' (sin .exe)
    cargar_env_local()
    validar_env()

    driver_path = os.getenv("CHROMEDRIVER_PATH")
    validar_chromedriver(driver_path)
    
    print(f"🚀 Iniciando bypass de Selenium Manager...")
    print(f"📍 Usando binario en: {driver_path}")

    # 2. Configuración robusta de Chrome
    chrome_options = Options()
    
    # Argumentos para evitar bloqueos en entornos Linux/Dell Latitude
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-features=PasswordLeakDetection")
    chrome_options.add_argument("--disable-save-password-bubble")
    chrome_options.add_argument("--disable-features=PasswordLeakDetection,SafeBrowsingPasswordCheck")
    chrome_options.add_argument("--disable-component-update") # Evita que Chrome busque actualizaciones de seguridad al abrir
    chrome_options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    })

    driver = None
    try:
        # 3. Forzar el inicio del Servicio
        # Al pasar el ejecutable directamente al Service, Selenium debería saltarse el Manager
        servicio = Service(executable_path=driver_path)
        
        print("⚙️  Lanzando instancia de navegador...")
        driver = webdriver.Chrome(service=servicio, options=chrome_options)
        print("✅ Navegador iniciado con éxito.")
        login(driver)

    except KeyboardInterrupt:
        print("\n🛑 Cierre solicitado por el usuario (Ctrl+C).")
        raise

    except Exception as e:
        print("\n--- INFORME DE ERROR DE INGENIERÍA ---")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje: {e}")
        print("---------------------------------------")
        print("\n💡 Tip rápido: Si el error persiste, intenta ejecutar:")
        print(f"chmod 777 {driver_path}")
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception as e:
                print(f"⚠️  Error al cerrar el navegador: {e}")

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
            os.environ.setdefault(key.strip(), value.strip())

def validar_env():
    faltantes = []

    if not os.getenv("CHROMEDRIVER_PATH"):
        faltantes.append("CHROMEDRIVER_PATH")
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
        raise SystemExit("CHROMEDRIVER_PATH no esta configurado en el .env.")

    if not os.path.isfile(driver_path):
        raise SystemExit(f"Chromedriver no encontrado en: {driver_path}")

    if os.name == "nt":
        if not driver_path.lower().endswith(".exe"):
            raise SystemExit("En Windows, CHROMEDRIVER_PATH debe terminar en .exe")
    else:
        if not os.access(driver_path, os.X_OK):
            raise SystemExit(f"Chromedriver no es ejecutable: {driver_path}")

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

def enviar_telegram(mensaje):
    token = os.getenv("TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token and not chat_id:
        return
    if not token or not chat_id:
        print("⚠️  Faltan TOKEN o CHAT_ID para Telegram.")
        return

    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": mensaje}).encode("utf-8")
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        with urllib.request.urlopen(url, data=payload, timeout=10) as response:
            if response.status != 200:
                print(f"⚠️  Error Telegram: HTTP {response.status}")
    except Exception as e:
        print(f"⚠️  Error enviando Telegram: {e}")

def telegram_habilitado():
    return bool(os.getenv("TOKEN") and os.getenv("CHAT_ID"))

def obtener_actualizaciones(offset):
    token = os.getenv("TOKEN")
    if not token:
        return [], offset

    params = urllib.parse.urlencode({"timeout": 0, "offset": offset}).encode("utf-8")
    url = f"https://api.telegram.org/bot{token}/getUpdates"

    try:
        with urllib.request.urlopen(url, data=params, timeout=10) as response:
            if response.status != 200:
                return [], offset
            payload = json.loads(response.read().decode("utf-8"))
            return payload.get("result", []), offset
    except Exception as e:
        print(f"⚠️  Error leyendo comandos de Telegram: {e}")
        return [], offset

def procesar_comandos_telegram(offset, estado):
    if not telegram_habilitado():
        return offset

    chat_id = os.getenv("CHAT_ID")
    updates, offset = obtener_actualizaciones(offset)

    for update in updates:
        update_id = update.get("update_id")
        if update_id is not None and update_id >= offset:
            offset = update_id + 1

        message = update.get("message") or {}
        text = (message.get("text") or "").strip()
        from_chat = message.get("chat", {}).get("id")

        if str(from_chat) != str(chat_id):
            continue
        if text == "/status":
            enviar_telegram(estado)

    return offset

def hilo_telegram(stop_event, estado_ref, estado_lock):
    offset = 0
    while not stop_event.is_set():
        with estado_lock:
            estado = estado_ref.get("texto", "Estado: iniciando")
        offset = procesar_comandos_telegram(offset, estado)
        sleep(3)

def login(driver):
    url = os.getenv("URL_LOGIN") or os.getenv("URL_UNI") or "https://usm.terna.net/"

    usuario = os.getenv("USER_UNI")
    contraseña = os.getenv("PASS_UNI")

    if not usuario or not contraseña:
        print("⚠️  Faltan USER_UNI o PASS_UNI en el .env.")
        return

    try:
        sleep(3)  # Espera inicial para asegurarse de que el navegador esté listo
        driver.get(url)

        print("🔐 Introduciendo credenciales...")

        campo_usuario = driver.find_element(By.NAME, "username")
        campo_usuario.send_keys(usuario)

        campo_contraseña = driver.find_element(By.NAME, "password")
        campo_contraseña.send_keys(contraseña)

        print("🚀 Enviando formulario de login...")

        boton_login = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        boton_login.click()

        # Pausa para verificar el resultado del login
        sleep(5)
        print("✅ Login realizado")
        botinscripcion(driver)

    
    except Exception as e:
        print("\n--- ERROR DURANTE EL LOGIN ---")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje: {e}")
        print(f"URL actual: {driver.current_url}")
        print("---------------------------------------")
        print("\n💡 Tip rápido: Asegúrate de que los selectores de los campos de usuario y contraseña sean correctos.")

def botinscripcion(driver):
    url = os.getenv("URL_INSCRIPCION") or "https://usm.terna.net/Inscripcion.php?mid=0"
    materias = cargar_materias()
    estado_ref = {"texto": "Estado: iniciando"}
    estado_lock = Lock()
    stop_event = Event()
    intentos = 0
    telegram_thread = None

    if telegram_habilitado():
        telegram_thread = Thread(
            target=hilo_telegram,
            args=(stop_event, estado_ref, estado_lock),
            daemon=True
        )
        telegram_thread.start()

    enviar_telegram("🟢 Bot de inscripcion iniciando...")

    driver.get(url)
    enviar_telegram("✅ Bot cargado. Esperando cupos...")

    try:
        while len(materias_pendientes(materias)) > 0:
            estado = construir_estado(materias, intentos)
            with estado_lock:
                estado_ref["texto"] = estado
            print("🤖 Bot de inscripción activo...")
            procesar_materias(driver, materias)

            if len(materias_pendientes(materias)) == 0:
                print("🎉 Todas las materias han sido inscritas.")
                enviar_telegram("🎉 Todas las materias han sido inscritas.")
                break

            sleep(40)  # Espera antes de recargar la página
            driver.refresh()
            intentos += 1
            print("🔄 Página recargada para verificar nuevas inscripciones.")
    except KeyboardInterrupt:
        print("\n🛑 Detenido por el usuario (Ctrl+C).")
        raise
    except Exception as e:
        print("\n--- ERROR DURANTE INSCRIPCIÓN ---")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje: {e}")
        print(f"URL actual: {driver.current_url}")
        print("---------------------------------------")
    finally:
        stop_event.set()
        if telegram_thread is not None:
            telegram_thread.join(timeout=5)
        enviar_telegram("🛑 Bot apagado.")

def procesar_materias(driver, materias):
    for nombre_materia, info in list(materias.items()):
        if info.get("inscrita"):
            continue

        secciones = info.get("secciones", [])
        # Coloca aqui la logica para ubicar la materia por nombre y abrirla.
        materia_inscrita = False

        for seccion in secciones:
            # Coloca aqui la logica para ubicar la seccion y presionar el boton.
            # Si la inscripcion fue exitosa, cambia materia_inscrita a True.
            materia_inscrita = False  # Ajusta a True cuando confirmes la inscripcion real

            if materia_inscrita:
                print(f"✅ Materia '{nombre_materia}' inscrita en seccion {seccion}.")
                enviar_telegram(f"🎯 Materia inscrita: {nombre_materia} | Seccion {seccion}")
                break

        if materia_inscrita:
            info["inscrita"] = True
            guardar_materias(materias)

if __name__ == "__main__":
    try:
        while True:
            iniciar_bot()
    except KeyboardInterrupt:
        print("\n🛑 Programa finalizado por el usuario.")