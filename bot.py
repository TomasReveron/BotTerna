from time import sleep
import os
from threading import Lock
from selenium import webdriver
import undetected_chromedriver as uc
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
    chrome_options = uc.ChromeOptions()

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
        print("⚙️  Lanzando instancia de navegador con undetected-chromedriver...")
        driver = uc.Chrome(
            options=chrome_options,
            driver_executable_path=driver_path
        )
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


def login(driver, ir_a_inscripcion=True):
    url = os.getenv("URL_LOGIN") or os.getenv("URL_UNI") or "https://usm.terna.net/"

    usuario = os.getenv("USER_UNI")
    contrasena = os.getenv("PASS_UNI")

    if not usuario or not contrasena:
        print("⚠️  Faltan USER_UNI o PASS_UNI en el .env.")
        return

    try:
        sleep(1)  # Espera para que el navegador este listo
        driver.get(url)
        if ir_a_inscripcion:
            input("Esperando...")
        sleep(5)
        print("🔐 Iniciando sesion...")

        campo_usuario = driver.find_element(By.NAME, "username")
        campo_usuario.send_keys(usuario)

        campo_contrasena = driver.find_element(By.NAME, "password")
        campo_contrasena.send_keys(contrasena)

        boton_login = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        boton_login.click()

        sleep(1)
        if ir_a_inscripcion:
            botinscripcion(driver)

    except Exception as e:
        print("\n--- ERROR DURANTE EL LOGIN ---")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje: {e}")
        print(f"URL actual: {driver.current_url}")
        print("---------------------------------------")
        print("\n💡 Tip rapido: Asegurate de que los selectores de los campos de usuario y contrasena sean correctos.")


def reloguear(driver):
    url_logout = "https://usm.terna.net/Logout.php?"
    try:
        driver.get(url_logout)
        sleep(1)
        login(driver, ir_a_inscripcion=False)
    except Exception as e:
        print(f"❌ Error durante el relogueo: {e}")


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

    notificacion_semestre_enviada = False
    notificacion_materias_enviada = False

    try:
        while len(materias_pendientes(materias)) > 0:
            # Revisar si se activó el semestre 202602
            if not notificacion_semestre_enviada:
                botones_202602 = driver.find_elements(By.XPATH, "//a[contains(text(), '202602')]")
                if len(botones_202602) > 0:
                    mensaje = "🚨 ¡ATENCIÓN! Ya activaron el botón del nuevo semestre (202602) en Pregrado Semestral."
                    print(mensaje)
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
                print("\n🎉 Todas las materias han sido inscritas.")
                enviar_telegram("🎉 Todas las materias han sido inscritas.")
                break

            # Mostrar progreso en una sola linea para no llenar la consola
            print(f"\r🤖 Intento {intentos} | Esperando cupos...", end="", flush=True)

            sleep(15)  # Espera optimizada
            reloguear(driver)
            driver.get(url)
            intentos += 1
            
            # Notificar cada 10 intentos
            if intentos % 10 == 0:
                mensaje_espera = f"⏳ Intento {intentos}: Aun no hay cupos..."
                print(mensaje_espera)
                enviar_telegram(mensaje_espera)
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
    materias_encontradas = False
    for nombre_materia, info in list(materias.items()):
        if info.get("inscrita"):
            continue

        secciones = info.get("secciones", [])
        materia_inscrita = False

        try:
            # Buscamos una fila (tr) de tabla que contenga el nombre de la materia (sin importar mayus/minus)
            nombre_upper = nombre_materia.upper()
            xpath_materia = f"//tr[contains(translate(., 'abcdefghijklmnopqrstuvwxyzáéíóú', 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚ'), '{nombre_upper}')]"
            filas_materia = driver.find_elements(By.XPATH, xpath_materia)

            if len(filas_materia) > 0:
                materias_encontradas = True
                fila = filas_materia[0]  # Tomamos la primera fila que coincida

                for seccion in secciones:
                    try:
                        # Buscamos un botón o enlace dentro de la fila de la materia que comience con el texto de la seccion seguido de ":"
                        xpath_seccion = f".//a[starts-with(normalize-space(text()), '{seccion}:')] | .//button[starts-with(normalize-space(text()), '{seccion}:')]"
                        botones_seccion = fila.find_elements(By.XPATH, xpath_seccion)

                        if len(botones_seccion) > 0:
                            boton = botones_seccion[0]
                            clase_boton = boton.get_attribute("class") or ""
                            texto_boton = boton.text.strip()
                            
                            # Extraer la cantidad de cupos (ej: "1MA:0" -> 0)
                            cupos = 0
                            try:
                                if ":" in texto_boton:
                                    cupos = int(texto_boton.split(":")[1].strip())
                            except ValueError:
                                pass # Si no se puede parsear a entero, asumimos 0 por seguridad

                            # Validar que el botón sea clicleable, no esté deshabilitado y tenga cupos > 0
                            if boton.is_enabled() and 'disabled' not in clase_boton.lower() and cupos > 0:
                                print(f"\n👉 Intentando inscribir '{nombre_materia}' en seccion {seccion}...")
                                # Clic vía JS, más resistente en caso de overlays o rediseños de la tabla
                                driver.execute_script("arguments[0].click();", boton)
                                sleep(1.5) # Pausa para que el servidor procese el clic
                                
                                materia_inscrita = True
                                print(f"✅ ¡Inscrita '{nombre_materia}' en seccion {seccion}!")
                                enviar_telegram(f"🎯 Exito: {nombre_materia} | Seccion {seccion}")
                                break # Ya la inscribimos, no necesitamos probar las demás secciones
                            # Seccion llena o inactiva (silencioso para evitar spam)
                                pass
                    except Exception:
                        pass
            
        except Exception as e:
            print(f"❌ Error buscando la materia '{nombre_materia}': {str(e)}")

        if materia_inscrita:
            info["inscrita"] = True
            guardar_materias(materias)

    return materias_encontradas
