from time import sleep
import os
from threading import Lock
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from config import cargar_env_local, validar_env, validar_chromedriver
from materias_store import cargar_materias, guardar_materias, materias_pendientes, construir_estado
from telegram_bot import enviar_telegram, iniciar_hilo_telegram


def iniciar_bot():
    # 1. Definir la ruta absoluta
    # Asegurate de que el nombre sea exactamente 'chromedriver' (sin .exe)
    cargar_env_local()
    validar_env()

    driver_path = os.getenv("CHROMEDRIVER_PATH")
    validar_chromedriver(driver_path)

    print("🚀 Iniciando bypass de Selenium Manager...")
    print(f"📍 Usando binario en: {driver_path}")

    # 2. Configuracion robusta de Chrome
    chrome_options = Options()

    # Argumentos para evitar bloqueos en entornos Linux/Dell Latitude
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-features=PasswordLeakDetection")
    chrome_options.add_argument("--disable-save-password-bubble")
    chrome_options.add_argument("--disable-features=PasswordLeakDetection,SafeBrowsingPasswordCheck")
    chrome_options.add_argument("--disable-component-update")
    chrome_options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    })

    driver = None
    try:
        # 3. Forzar el inicio del Servicio
        servicio = Service(executable_path=driver_path)

        print("⚙️  Lanzando instancia de navegador...")
        driver = webdriver.Chrome(service=servicio, options=chrome_options)
        print("✅ Navegador iniciado con exito.")
        login(driver)

    except KeyboardInterrupt:
        print("\n🛑 Cierre solicitado por el usuario (Ctrl+C).")
        raise

    except Exception as e:
        print("\n--- INFORME DE ERROR DE INGENIERIA ---")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje: {e}")
        print("---------------------------------------")
        print("\n💡 Tip rapido: Si el error persiste, intenta ejecutar:")
        print(f"chmod 777 {driver_path}")
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception as e:
                print(f"⚠️  Error al cerrar el navegador: {e}")


def login(driver):
    url = os.getenv("URL_LOGIN") or os.getenv("URL_UNI") or "https://usm.terna.net/"

    usuario = os.getenv("USER_UNI")
    contrasena = os.getenv("PASS_UNI")

    if not usuario or not contrasena:
        print("⚠️  Faltan USER_UNI o PASS_UNI en el .env.")
        return

    try:
        sleep(3)  # Espera inicial para asegurarse de que el navegador este listo
        driver.get(url)

        print("🔐 Introduciendo credenciales...")

        campo_usuario = driver.find_element(By.NAME, "username")
        campo_usuario.send_keys(usuario)

        campo_contrasena = driver.find_element(By.NAME, "password")
        campo_contrasena.send_keys(contrasena)

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
        print("\n💡 Tip rapido: Asegurate de que los selectores de los campos de usuario y contrasena sean correctos.")


def botinscripcion(driver):
    url = os.getenv("URL_INSCRIPCION") or "https://usm.terna.net/Inscripcion.php?mid=0"
    materias = cargar_materias()
    estado_ref = {"texto": "Estado: iniciando"}
    estado_lock = Lock()
    intentos = 0

    stop_event, telegram_thread = iniciar_hilo_telegram(estado_ref, estado_lock)

    enviar_telegram("🟢 Bot de inscripcion iniciando...")

    driver.get(url)
    enviar_telegram("✅ Bot cargado. Esperando cupos...")

    try:
        while len(materias_pendientes(materias)) > 0:
            estado = construir_estado(materias, intentos)
            with estado_lock:
                estado_ref["texto"] = estado
            print("🤖 Bot de inscripcion activo...")
            procesar_materias(driver, materias)

            if len(materias_pendientes(materias)) == 0:
                print("🎉 Todas las materias han sido inscritas.")
                enviar_telegram("🎉 Todas las materias han sido inscritas.")
                break

            sleep(40)  # Espera antes de recargar la pagina
            driver.refresh()
            intentos += 1
            print("🔄 Pagina recargada para verificar nuevas inscripciones.")
    except KeyboardInterrupt:
        print("\n🛑 Detenido por el usuario (Ctrl+C).")
        raise
    except Exception as e:
        print("\n--- ERROR DURANTE INSCRIPCION ---")
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
