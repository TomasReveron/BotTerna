from time import sleep
import os
from threading import Lock
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import cargar_env_local, validar_env, validar_chromedriver, obtener_ruta_perfil_chrome
from materias_store import cargar_materias, guardar_materias, materias_pendientes, construir_estado
from telegram_bot import enviar_telegram, iniciar_hilo_telegram


def iniciar_bot():
    cargar_env_local()
    validar_env()

    driver_path = os.getenv("CHROMEDRIVER_PATH")
    if driver_path:
        validar_chromedriver(driver_path)
    user_data_dir = obtener_ruta_perfil_chrome()

    print("🚀 Iniciando bypass con undetected-chromedriver y perfil persistente...")
    if driver_path:
        print(f"📍 Usando binario manual en: {driver_path}")
    else:
        print("📍 Modo automático: undetected-chromedriver gestionará el driver matching de Chrome.")
    print(f"📁 Perfil de Chrome en: {user_data_dir}")

    # Configuración de Chrome con perfil persistente para evitar bloqueos de Cloudflare
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    if os.name != "nt":
        chrome_options.add_argument("--ozone-platform-hint=auto")  # Soporte nativo para Wayland/Linux
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-features=PasswordLeakDetection,SafeBrowsingPasswordCheck")
    chrome_options.add_argument("--disable-save-password-bubble")
    chrome_options.add_argument("--disable-component-update")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")

    headless = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")
    if headless:
        print("🕶️  Modo Headless activado.")
        chrome_options.add_argument("--headless=new")
    else:
        # Ventana visible normalmente en pantalla
        chrome_options.add_argument("--window-size=1280,800")

    chrome_options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    })

    driver_kwargs = {"options": chrome_options}
    if driver_path:
        driver_kwargs["driver_executable_path"] = driver_path

    driver = None
    exito_total = False
    try:
        print("⚙️  Lanzando instancia de navegador...")
        driver = uc.Chrome(**driver_kwargs)
        print("✅ Navegador iniciado con éxito.")
        
        login(driver)
        exito_total = botinscripcion(driver)
        return exito_total

    except KeyboardInterrupt:
        print("\n🛑 Cierre solicitado por el usuario (Ctrl+C).")
        raise

    except Exception as e:
        print("\n--- INFORME DE ERROR ---")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje: {e}")
        print("------------------------")
        return False
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception as e:
                print(f"⚠️  Error al cerrar el navegador: {e}")


def login(driver, timeout=10):
    url = os.getenv("URL_LOGIN") or os.getenv("URL_UNI") or "https://usm.terna.net/"
    usuario = os.getenv("USER_UNI")
    contrasena = os.getenv("PASS_UNI")

    if not usuario or not contrasena:
        print("⚠️  Faltan USER_UNI o PASS_UNI en el .env.")
        return False

    try:
        driver.get(url)
        wait = WebDriverWait(driver, timeout)

        # Esperar inmediatamente a que el formulario esté disponible
        campo_usuario = wait.until(EC.visibility_of_element_located((By.NAME, "username")))
        campo_usuario.clear()
        campo_usuario.send_keys(usuario)

        campo_contrasena = wait.until(EC.visibility_of_element_located((By.NAME, "password")))
        campo_contrasena.clear()
        campo_contrasena.send_keys(contrasena)

        boton_login = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")))
        boton_login.click()

        sleep(0.8)
        return True

    except Exception as e:
        # Si ya había sesión o no hay formulario visible, continúa
        return False


def reloguear(driver):
    url_logout = "https://usm.terna.net/Logout.php?"
    try:
        driver.get(url_logout)
        sleep(0.5)
        login(driver)
    except Exception as e:
        print(f"\n❌ Error durante el relogueo: {e}")


def botinscripcion(driver):
    url = os.getenv("URL_INSCRIPCION") or "https://usm.terna.net/Inscripcion.php?mid=0"
    materias = cargar_materias()
    estado_ref = {"texto": "Estado: iniciando"}
    estado_lock = Lock()
    intentos = 0

    stop_event, telegram_thread = iniciar_hilo_telegram(estado_ref, estado_lock)

    enviar_telegram("🟢 Bot de inscripción iniciando...")
    driver.get(url)
    enviar_telegram("✅ Bot cargado. Esperando cupos...")

    notificacion_semestre_enviada = False
    notificacion_materias_enviada = False

    try:
        while len(materias_pendientes(materias)) > 0:
            # Revisar si se activó el semestre nuevo en Pregrado Semestral
            if not notificacion_semestre_enviada:
                botones_semestre = driver.find_elements(
                    By.XPATH, 
                    "//a[contains(text(), '202602') or contains(text(), '2026-2') or contains(text(), '2026-II')]"
                )
                if len(botones_semestre) > 0:
                    mensaje = "🚨 ¡ATENCIÓN! Ya activaron el botón del nuevo semestre en Pregrado Semestral."
                    print(f"\n{mensaje}")
                    enviar_telegram(mensaje)
                    notificacion_semestre_enviada = True

            estado = construir_estado(materias, intentos)
            with estado_lock:
                estado_ref["texto"] = estado

            materias_visibles = procesar_materias(driver, materias)

            if materias_visibles and not notificacion_materias_enviada:
                mensaje = "👀 ¡Las materias ya aparecieron!"
                print(f"\n{mensaje}")
                enviar_telegram(mensaje)
                notificacion_materias_enviada = True

            if len(materias_pendientes(materias)) == 0:
                print("\n🎉 ¡Todas las materias han sido inscritas exitosamente!")
                enviar_telegram("🎉 ¡Todas las materias han sido inscritas exitosamente!")
                return True

            intentos += 1
            print(f"\r🤖 Intento {intentos} | Relogueando y verificando cupos...", end="", flush=True)

            # Notificar periódicamente por Telegram cada 15 intentos
            if intentos % 15 == 0:
                mensaje_espera = f"⏳ Intento {intentos}: Monitoreando cupos activamente..."
                enviar_telegram(mensaje_espera)

            # Relogueo rápido y recarga inmediata de la página de inscripción
            reloguear(driver)
            driver.get(url)

    except KeyboardInterrupt:
        print("\n🛑 Detenido por el usuario (Ctrl+C).")
        raise
    except Exception as e:
        error_str = str(e)
        if "no such window" in error_str or "target window already closed" in error_str:
            print("\n⚠️  La ventana del navegador fue cerrada.")
        else:
            print("\n--- ERROR DURANTE INSCRIPCIÓN ---")
            print(f"Tipo de error: {type(e).__name__}")
            print(f"Mensaje: {e}")
            print("---------------------------------------")
        return False
    finally:
        stop_event.set()
        if telegram_thread is not None:
            telegram_thread.join(timeout=3)
        if len(materias_pendientes(materias)) == 0:
            enviar_telegram("🎯 Bot finalizado: Proceso completado con éxito.")
        else:
            enviar_telegram("🛑 Bot detenido.")

    return len(materias_pendientes(materias)) == 0


def procesar_materias(driver, materias):
    materias_encontradas = False
    for nombre_materia, info in list(materias.items()):
        if info.get("inscrita"):
            continue

        secciones = info.get("secciones", [])
        materia_inscrita = False

        try:
            # Búsqueda robusta insensible a mayúsculas y acentos
            nombre_upper = nombre_materia.upper()
            xpath_materia = f"//tr[contains(translate(., 'abcdefghijklmnopqrstuvwxyzáéíóúüñ', 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ'), '{nombre_upper}')]"
            filas_materia = driver.find_elements(By.XPATH, xpath_materia)

            if len(filas_materia) > 0:
                materias_encontradas = True
                fila = filas_materia[0]

                for seccion in secciones:
                    try:
                        xpath_seccion = f".//a[starts-with(normalize-space(.), '{seccion}:')] | .//button[starts-with(normalize-space(.), '{seccion}:')]"
                        botones_seccion = fila.find_elements(By.XPATH, xpath_seccion)

                        if len(botones_seccion) > 0:
                            boton = botones_seccion[0]
                            clase_boton = boton.get_attribute("class") or ""
                            texto_boton = boton.text.strip()
                            
                            cupos = 0
                            try:
                                if ":" in texto_boton:
                                    cupos = int(texto_boton.split(":")[1].strip())
                            except ValueError:
                                pass

                            if boton.is_enabled() and 'disabled' not in clase_boton.lower() and cupos > 0:
                                print(f"\n👉 ¡Cupo detectado ({cupos})! Inscribiendo '{nombre_materia}' en sección {seccion}...")
                                driver.execute_script("arguments[0].click();", boton)
                                sleep(1.0)
                                
                                materia_inscrita = True
                                print(f"✅ ¡Inscrita '{nombre_materia}' en sección {seccion}!")
                                enviar_telegram(f"🎯 Éxito: {nombre_materia} | Sección {seccion} (Cupos: {cupos})")
                                break
                    except Exception:
                        pass
            
        except Exception as e:
            print(f"\n❌ Error buscando la materia '{nombre_materia}': {str(e)}")

        if materia_inscrita:
            info["inscrita"] = True
            guardar_materias(materias)

    return materias_encontradas
