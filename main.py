from time import sleep
import os
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
    if not os.getenv("TOKEN"):
        faltantes.append("TOKEN")
    if not os.getenv("CHAT_ID"):
        faltantes.append("CHAT_ID")

    if faltantes:
        print("⚠️  Faltan variables en el .env: " + ", ".join(faltantes))
        raise SystemExit("No se puede continuar sin estas variables.")

def enviar_telegram(mensaje):
    token = os.getenv("TOKEN")
    chat_id = os.getenv("CHAT_ID")

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

def login(driver):
    cargar_env_local()
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
    cargar_env_local()
    url = os.getenv("URL_INSCRIPCION") or "https://usm.terna.net/Inscripcion.php?mid=0"
    materias = {
        "BASE DE DATOS": ["1MB"],
        "INGENIERIA SOFTWARE I": ["1MA"],
        "INVEST. DE OPERACIONES II": ["1MA"],
    }

    driver.get(url)

    try:
        while len(materias) > 0:
            print("🤖 Bot de inscripción activo...")
            procesar_materias(driver, materias)

            if len(materias) == 0:
                print("🎉 Todas las materias han sido inscritas.")
                enviar_telegram("🎉 Todas las materias han sido inscritas.")
                break

            sleep(40)  # Espera antes de recargar la página
            driver.refresh()
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

def procesar_materias(driver, materias):
    for nombre_materia, secciones in list(materias.items()):
        # Coloca aqui la logica para ubicar la materia por nombre y abrirla.
        materia_inscrita = False

        for seccion in secciones:
            # Coloca aqui la logica para ubicar la seccion y presionar el boton.
            # Si la inscripcion fue exitosa, cambia materia_inscrita a True.
            materia_inscrita = False  # Ajusta a True cuando confirmes la inscripcion real

            if materia_inscrita:
                print(f"✅ Materia '{nombre_materia}' inscrita en seccion {seccion}.")
                enviar_telegram(f"Materia inscrita: {nombre_materia} - Seccion {seccion}")
                break

        if materia_inscrita:
            materias.pop(nombre_materia, None)

if __name__ == "__main__":
    try:
        while True:
            iniciar_bot()
    except KeyboardInterrupt:
        print("\n🛑 Programa finalizado por el usuario.")