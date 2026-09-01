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


def _emit(log_callback, level, message, data=None):
    if log_callback:
        try:
            log_callback(level, message, data)
        except Exception:
            pass


def iniciar_bot(stop_event=None, log_callback=None):
    cargar_env_local()
    validar_env()

    driver_path = os.getenv("CHROMEDRIVER_PATH")
    if driver_path:
        validar_chromedriver(driver_path)
    user_data_dir = obtener_ruta_perfil_chrome()

    msg_init = "🚀 Iniciando bypass con undetected-chromedriver y perfil persistente..."
    print(msg_init)
    _emit(log_callback, "info", msg_init)

    if driver_path:
        print(f"📍 Usando binario manual en: {driver_path}")
        _emit(log_callback, "info", f"📍 Usando binario manual en: {driver_path}")
    else:
        print("📍 Modo automático: undetected-chromedriver gestionará el driver matching de Chrome.")
        _emit(log_callback, "info", "📍 Modo automático: gestión automática de ChromeDriver.")
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
        _emit(log_callback, "info", "🕶️ Modo Headless activado (navegador en segundo plano).")
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
        msg_launch = "⚙️  Lanzando instancia de navegador..."
        print(msg_launch)
        _emit(log_callback, "info", msg_launch)

        if stop_event and stop_event.is_set():
            return False

        driver = uc.Chrome(**driver_kwargs)
        msg_ready = "✅ Navegador iniciado con éxito."
        print(msg_ready)
        _emit(log_callback, "success", msg_ready)
        
        if stop_event and stop_event.is_set():
            return False

        login(driver, log_callback=log_callback)
        exito_total = botinscripcion(driver, stop_event=stop_event, log_callback=log_callback)
        return exito_total

    except KeyboardInterrupt:
        print("\n🛑 Cierre solicitado por el usuario (Ctrl+C).")
        _emit(log_callback, "warning", "🛑 Detenido por el usuario.")
        raise

    except Exception as e:
        print("\n--- INFORME DE ERROR ---")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje: {e}")
        print("------------------------")
        _emit(log_callback, "error", f"Error ({type(e).__name__}): {e}")
        return False
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception as e:
                print(f"⚠️  Error al cerrar el navegador: {e}")


def login(driver, timeout=10, log_callback=None):
    url = os.getenv("URL_LOGIN") or os.getenv("URL_UNI") or "https://usm.terna.net/"
    usuario = os.getenv("USER_UNI")
    contrasena = os.getenv("PASS_UNI")

    if not usuario or not contrasena:
        msg = "⚠️ Faltan USER_UNI o PASS_UNI en la configuración. Revisa tus credenciales."
        print(f"\n{msg}")
        _emit(log_callback, "login_failed", msg, {"tipo": "credenciales_vacias"})
        return False

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 4)

        # Verificar si ya existe sesión abierta
        if "Logout.php" in driver.page_source or len(driver.find_elements(By.XPATH, "//a[contains(@href, 'Logout')]")) > 0:
            _emit(log_callback, "info", "🔑 Sesión activa verificada en Terna.")
            return True

        # Esperar campos de formulario
        try:
            campo_usuario = wait.until(EC.visibility_of_element_located((By.NAME, "username")))
        except Exception:
            if "Logout.php" in driver.page_source or "Inscripcion.php" in driver.current_url:
                _emit(log_callback, "info", "🔑 Sesión activa detectada.")
                return True
            _emit(log_callback, "warning", "⚠️ Formulario de inicio de sesión no encontrado.")
            return False

        campo_usuario.clear()
        campo_usuario.send_keys(usuario)

        campo_contrasena = driver.find_element(By.NAME, "password")
        campo_contrasena.clear()
        campo_contrasena.send_keys(contrasena)

        boton_login = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        boton_login.click()

        sleep(1.2)

        # VERIFICACIÓN DE LOGIN EXITOSO VS ERROR
        campos_visibles = driver.find_elements(By.NAME, "username")
        alerta_error = driver.find_elements(By.CLASS_NAME, "alert-danger") or driver.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(text(), 'incorrect') or contains(text(), 'inválid') or contains(text(), 'invalida') or contains(text(), 'Error')]")

        if len(campos_visibles) > 0 and len(alerta_error) > 0:
            texto_error = alerta_error[0].text.strip() if alerta_error else "Credenciales incorrectas"
            msg = f"🚨 ERROR DE LOGIN EN TERNA: {texto_error}. Revisa tu usuario y contraseña en Configuración."
            print(f"\n{msg}")
            enviar_telegram(msg)
            _emit(log_callback, "login_failed", msg, {"tipo": "credenciales_invalidas", "error": texto_error})
            return False

        _emit(log_callback, "info", "🔑 Sesión iniciada correctamente en Terna.")
        return True

    except Exception as e:
        msg = f"⚠️ Error al conectar con Terna para iniciar sesión: {e}"
        _emit(log_callback, "login_failed", msg, {"tipo": "conexion", "error": str(e)})
        return False


def reloguear(driver, log_callback=None):
    url_logout = "https://usm.terna.net/Logout.php?"
    try:
        driver.get(url_logout)
        sleep(0.5)
        return login(driver, log_callback=log_callback)
    except Exception as e:
        print(f"\n❌ Error durante el relogueo: {e}")
        return False


def botinscripcion(driver, stop_event=None, log_callback=None):
    url = os.getenv("URL_INSCRIPCION") or "https://usm.terna.net/Inscripcion.php?mid=0"
    materias = cargar_materias()
    estado_ref = {"texto": "Estado: iniciando"}
    estado_lock = Lock()
    intentos = 0

    tg_stop_event, telegram_thread = iniciar_hilo_telegram(estado_ref, estado_lock)

    enviar_telegram("🟢 Bot de inscripción iniciando...")
    _emit(log_callback, "info", "🟢 Accediendo al portal de inscripción...")
    driver.get(url)

    # Verificar si fue redirigido al login por falta de sesión
    if len(driver.find_elements(By.NAME, "username")) > 0 or "login" in driver.current_url.lower():
        _emit(log_callback, "warning", "⚠️ Sesión inactiva detectada. Autenticando...")
        login_ok = login(driver, log_callback=log_callback)
        if not login_ok:
            _emit(log_callback, "login_failed", "🚨 ALERTA: No se pudo iniciar sesión. Verifica tu usuario y contraseña.", {"tipo": "login_fallido"})
        driver.get(url)

    enviar_telegram("✅ Bot cargado. Esperando cupos...")
    _emit(log_callback, "success", "✅ Conectado a Terna. Monitoreando cupos...")

    notificacion_semestre_enviada = False
    notificacion_materias_enviada = False

    try:
        while len(materias_pendientes(materias)) > 0:
            if stop_event and stop_event.is_set():
                _emit(log_callback, "warning", "🛑 Detención solicitada. Finalizando proceso...")
                break

            # Revisar si se activó el semestre nuevo en Pregrado Semestral (202701 o variaciones)
            if not notificacion_semestre_enviada:
                botones_semestre = driver.find_elements(
                    By.XPATH, 
                    "//a[contains(text(), '202701') or contains(text(), '2027-1') or contains(text(), '2027-I') or contains(text(), '2027-01') or contains(text(), '2027/1') or contains(text(), '20271')]"
                )
                if len(botones_semestre) > 0:
                    mensaje = "🚨 ¡ATENCIÓN! Ya activaron el botón del nuevo semestre (202701) en Pregrado Semestral."
                    print(f"\n{mensaje}")
                    enviar_telegram(mensaje)
                    _emit(log_callback, "warning", mensaje)
                    notificacion_semestre_enviada = True

            estado = construir_estado(materias, intentos)
            with estado_lock:
                estado_ref["texto"] = estado

            materias_visibles = procesar_materias(driver, materias, log_callback=log_callback)

            if materias_visibles and not notificacion_materias_enviada:
                mensaje = "👀 ¡Las materias ya aparecieron en la lista!"
                print(f"\n{mensaje}")
                enviar_telegram(mensaje)
                _emit(log_callback, "info", mensaje)
                notificacion_materias_enviada = True

            pendientes = materias_pendientes(materias)
            inscritas = len(materias) - len(pendientes)
            if len(pendientes) == 0:
                print("\n🎉 ¡Todas las materias han sido inscritas exitosamente!")
                enviar_telegram("🎉 ¡Todas las materias han sido inscritas exitosamente!")
                _emit(log_callback, "success", "🎉 ¡Todas las materias han sido inscritas exitosamente!", {"status": "completado", "pendientes": 0, "inscritas": inscritas, "intentos": intentos})
                return True

            intentos += 1
            print(f"\r🤖 Intento {intentos} | Relogueando y verificando cupos...", end="", flush=True)
            _emit(log_callback, "attempt", f"Intento {intentos} | Verificando cupos y refrescando...", {"intentos": intentos, "pendientes": len(pendientes), "inscritas": inscritas})

            # Notificar periódicamente por Telegram cada 15 intentos
            if intentos % 15 == 0:
                mensaje_espera = f"⏳ Intento {intentos}: Monitoreando cupos activamente..."
                enviar_telegram(mensaje_espera)

            if stop_event and stop_event.is_set():
                break

            # Relogueo rápido y recarga inmediata de la página de inscripción
            reloguear(driver, log_callback=log_callback)
            driver.get(url)

    except KeyboardInterrupt:
        print("\n🛑 Detenido por el usuario (Ctrl+C).")
        raise
    except Exception as e:
        error_str = str(e)
        if "no such window" in error_str or "target window already closed" in error_str:
            print("\n⚠️  La ventana del navegador fue cerrada.")
            _emit(log_callback, "warning", "⚠️ La ventana del navegador fue cerrada.")
        else:
            print("\n--- ERROR DURANTE INSCRIPCIÓN ---")
            print(f"Tipo de error: {type(e).__name__}")
            print(f"Mensaje: {e}")
            print("---------------------------------------")
            _emit(log_callback, "error", f"Error en ciclo de inscripción: {e}")
        return False
    finally:
        tg_stop_event.set()
        if telegram_thread is not None:
            telegram_thread.join(timeout=3)
        if len(materias_pendientes(materias)) == 0:
            enviar_telegram("🎯 Bot finalizado: Proceso completado con éxito.")
        else:
            enviar_telegram("🛑 Bot detenido.")

    return len(materias_pendientes(materias)) == 0


def procesar_materias(driver, materias, log_callback=None):
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
                                log_cupo = f"👉 ¡Cupo detectado ({cupos})! Inscribiendo '{nombre_materia}' en sección {seccion}..."
                                print(f"\n{log_cupo}")
                                _emit(log_callback, "success", log_cupo)
                                driver.execute_script("arguments[0].click();", boton)
                                sleep(1.0)
                                
                                materia_inscrita = True
                                log_ok = f"✅ ¡Inscrita '{nombre_materia}' en sección {seccion}!"
                                print(log_ok)
                                _emit(log_callback, "success", log_ok, {"materia": nombre_materia, "seccion": seccion, "inscrita": True})
                                enviar_telegram(f"🎯 Éxito: {nombre_materia} | Sección {seccion} (Cupos: {cupos})")
                                break
                    except Exception:
                        pass
            
        except Exception as e:
            msg_err = f"❌ Error buscando la materia '{nombre_materia}': {str(e)}"
            print(f"\n{msg_err}")
            _emit(log_callback, "error", msg_err)

        if materia_inscrita:
            info["inscrita"] = True
            guardar_materias(materias)

    return materias_encontradas
