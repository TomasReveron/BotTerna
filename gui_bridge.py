import json
import os
import threading
import time
import requests
from config import cargar_env_local, obtener_ruta_perfil_chrome, obtener_ruta_base
from materias_store import cargar_materias, guardar_materias, materias_pendientes
from bot import iniciar_bot
from license_manager import (
    verificar_estado_licencia,
    activar_clave_licencia,
    obtener_hardware_id
)


class BotBridgeApi:
    def __init__(self):
        self.window = None
        self.bot_thread = None
        self.stop_event = threading.Event()
        self.is_running = False
        self.logs_buffer = []
        self.stats = {
            "intentos": 0,
            "materias_pendientes": 0,
            "estado": "Inactivo",
            "inicio_tiempo": None
        }

    # ------------------ SISTEMA DE LICENCIA ------------------
    def get_license_status(self):
        return verificar_estado_licencia()

    def activate_license(self, key):
        res = activar_clave_licencia(key)
        if res.get("success"):
            self._emit_to_ui("license_activated", res)
        return res

    def get_hardware_id(self):
        return {"hwid": obtener_hardware_id()}

    def set_window(self, window):
        self.window = window

    def _emit_to_ui(self, event_type, data):
        if self.window:
            try:
                payload = json.dumps({"type": event_type, "data": data}, ensure_ascii=False)
                self.window.evaluate_js(f"window.onBridgeEvent && window.onBridgeEvent({payload});")
            except Exception:
                pass

    def _log_callback(self, level, message, data=None):
        timestamp = time.strftime("%H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "data": data or {}
        }
        self.logs_buffer.append(log_entry)
        if len(self.logs_buffer) > 300:
            self.logs_buffer.pop(0)

        if data and "intentos" in data:
            self.stats["intentos"] = data["intentos"]
        if data and "pendientes" in data:
            self.stats["materias_pendientes"] = data["pendientes"]
        if data and "inscritas" in data:
            self.stats["materias_inscritas"] = data["inscritas"]

        self._emit_to_ui("log", log_entry)
        self._emit_to_ui("stats_updated", self.stats)

        if level == "login_failed":
            self._emit_to_ui("login_failed", {
                "message": message,
                "data": data or {}
            })

    # ------------------ CONFIGURACIÓN ------------------
    def get_config(self):
        env_path = os.path.join(obtener_ruta_base(estatico=False), ".env")
        config = {
            "USER_UNI": "",
            "PASS_UNI": "",
            "URL_LOGIN": "https://usm.terna.net/",
            "URL_INSCRIPCION": "https://usm.terna.net/Inscripcion.php?mid=0",
            "TOKEN": "",
            "CHAT_ID": "",
            "HEADLESS": False,
            "CHROMEDRIVER_PATH": ""
        }
        if os.path.isfile(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    if key in config:
                        if key == "HEADLESS":
                            config[key] = val.lower() in ("true", "1", "yes")
                        else:
                            config[key] = val
                    os.environ[key] = val
        return config

    def save_config(self, config_data):
        env_path = os.path.join(obtener_ruta_base(estatico=False), ".env")
        lines = []
        
        # Read existing file to preserve comments if possible, or build a clean one
        user_uni = config_data.get("USER_UNI", "").strip()
        pass_uni = config_data.get("PASS_UNI", "").strip()
        url_login = config_data.get("URL_LOGIN", "https://usm.terna.net/").strip()
        url_inscripcion = config_data.get("URL_INSCRIPCION", "https://usm.terna.net/Inscripcion.php?mid=0").strip()
        token = config_data.get("TOKEN", "").strip()
        chat_id = config_data.get("CHAT_ID", "").strip()
        headless = "true" if config_data.get("HEADLESS") else "false"
        driver_path = config_data.get("CHROMEDRIVER_PATH", "").strip()

        env_content = f"""# CREDENCIALES TERNA
USER_UNI={user_uni}
PASS_UNI={pass_uni}

# URLS TERNA
URL_LOGIN={url_login}
URL_INSCRIPCION={url_inscripcion}

# TELEGRAM
TOKEN={token}
CHAT_ID={chat_id}

# MODO VISUALIZACION
HEADLESS={headless}

# DRIVER (Opcional)
CHROMEDRIVER_PATH={driver_path}
"""
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content)

        # Actualizar variables en tiempo de ejecución
        os.environ["USER_UNI"] = user_uni
        os.environ["PASS_UNI"] = pass_uni
        os.environ["URL_LOGIN"] = url_login
        os.environ["URL_INSCRIPCION"] = url_inscripcion
        os.environ["TOKEN"] = token
        os.environ["CHAT_ID"] = chat_id
        os.environ["HEADLESS"] = headless
        os.environ["CHROMEDRIVER_PATH"] = driver_path

        return {"success": True, "message": "Configuración guardada exitosamente."}

    def test_telegram(self, token, chat_id):
        default_token = "8460968012:AAHOs7i8kWrg0Y5XNBCGWXU-gOSUzW41zcA"
        token = token.strip() if token else (os.getenv("TOKEN") or default_token)
        chat_id = chat_id.strip() if chat_id else os.getenv("CHAT_ID", "")

        if not chat_id:
            return {"success": False, "message": "Por favor ingresa tu Chat ID de Telegram."}

        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": "🤖 *BotTerna Test*: ¡Conexión exitosa con Telegram! Recibirás alertas aquí cuando haya cupos disponibles.",
                "parse_mode": "Markdown"
            }
            resp = requests.post(url, data=payload, timeout=8)
            res_json = resp.json()
            if res_json.get("ok"):
                return {"success": True, "message": "¡Mensaje de prueba enviado exitosamente a tu Telegram!"}
            else:
                return {"success": False, "message": f"Error de Telegram: {res_json.get('description')}"}
        except Exception as e:
            return {"success": False, "message": f"Fallo al conectar con Telegram: {str(e)}"}

    # ------------------ MATERIAS ------------------
    def get_materias(self):
        try:
            return {"success": True, "materias": cargar_materias()}
        except Exception as e:
            return {"success": False, "error": str(e), "materias": {}}

    def save_materias(self, materias_dict):
        try:
            guardar_materias(materias_dict)
            self._emit_to_ui("materias_updated", materias_dict)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_materia(self, nombre, secciones):
        nombre = nombre.strip().upper()
        if not nombre:
            return {"success": False, "message": "El nombre de la materia no puede estar vacío."}

        if isinstance(secciones, str):
            secciones = [s.strip().upper() for s in secciones.split(",") if s.strip()]

        if not secciones:
            return {"success": False, "message": "Debes agregar al menos una sección."}

        materias = cargar_materias()
        materias[nombre] = {
            "secciones": secciones,
            "inscrita": False
        }
        guardar_materias(materias)
        self._emit_to_ui("materias_updated", materias)
    def edit_materia(self, old_nombre, new_nombre, new_secciones):
        old_nombre = old_nombre.strip().upper()
        new_nombre = new_nombre.strip().upper()

        if not new_nombre:
            return {"success": False, "message": "El nombre de la materia no puede estar vacío."}

        if isinstance(new_secciones, str):
            new_secciones = [s.strip().upper() for s in new_secciones.split(",") if s.strip()]

        if not new_secciones:
            return {"success": False, "message": "Debes incluir al menos una sección."}

        materias = cargar_materias()
        if old_nombre not in materias:
            return {"success": False, "message": "La materia a editar no existe."}

        estado_previo = materias[old_nombre].get("inscrita", False)

        if old_nombre != new_nombre and new_nombre in materias:
            return {"success": False, "message": f"Ya existe otra materia llamada '{new_nombre}'."}

        if old_nombre != new_nombre:
            del materias[old_nombre]

        materias[new_nombre] = {
            "secciones": new_secciones,
            "inscrita": estado_previo
        }

        guardar_materias(materias)
        self._emit_to_ui("materias_updated", materias)
        return {"success": True, "materias": materias}

    def delete_materia(self, nombre):
        materias = cargar_materias()
        if nombre in materias:
            del materias[nombre]
            guardar_materias(materias)
            self._emit_to_ui("materias_updated", materias)
            return {"success": True, "materias": materias}
        return {"success": False, "message": "Materia no encontrada."}

    def toggle_materia_inscrita(self, nombre, status):
        materias = cargar_materias()
        if nombre in materias:
            materias[nombre]["inscrita"] = bool(status)
            guardar_materias(materias)
            self._emit_to_ui("materias_updated", materias)
            return {"success": True, "materias": materias}
        return {"success": False, "message": "Materia no encontrada."}

    def update_secciones(self, nombre, secciones):
        materias = cargar_materias()
        if nombre in materias:
            materias[nombre]["secciones"] = secciones
            guardar_materias(materias)
            self._emit_to_ui("materias_updated", materias)
            return {"success": True, "materias": materias}
        return {"success": False, "message": "Materia no encontrada."}

    # ------------------ CONTROL DEL BOT ------------------
    def start_bot(self):
        if self.is_running:
            return {"success": False, "message": "El bot ya se encuentra en ejecución."}

        # Validar licencia activa en Google Sheets
        lic_stat = verificar_estado_licencia()
        if not lic_stat.get("active"):
            self._emit_to_ui("license_revoked", {
                "message": lic_stat.get("message", "Esta licencia fue invalidada o revocada por el administrador.")
            })
            return {
                "success": False, 
                "message": lic_stat.get("message", "Se requiere una clave de activación activa para ejecutar el bot.")
            }

        materias = cargar_materias()
        pendientes = materias_pendientes(materias)
        if len(pendientes) == 0:
            return {
                "success": False, 
                "message": "Todas las materias están marcadas como inscritas. Desmarca alguna para iniciar."
            }

        self.stop_event.clear()
        self.is_running = True
        self.stats["estado"] = "Ejecutando"
        self.stats["intentos"] = 0
        self.stats["materias_pendientes"] = len(pendientes)
        self.stats["inicio_tiempo"] = time.time()

        self._emit_to_ui("bot_status", {"running": True, "stats": self.stats})

        def run_worker():
            try:
                self._log_callback("info", "🚀 Iniciando ciclo del bot desde la interfaz...")
                while not self.stop_event.is_set():
                    exito = iniciar_bot(stop_event=self.stop_event, log_callback=self._log_callback)
                    if exito or self.stop_event.is_set():
                        break

                    # Revisar si se terminaron las materias
                    mat_check = cargar_materias()
                    if len(materias_pendientes(mat_check)) == 0:
                        break

                    if not self.stop_event.is_set():
                        self._log_callback("info", "🔄 Reiniciando navegador en 3 segundos...")
                        for _ in range(6):
                            if self.stop_event.is_set():
                                break
                            time.sleep(0.5)

            except Exception as e:
                self._log_callback("error", f"Excepción en hilo del bot: {str(e)}")
            finally:
                self.is_running = False
                self.stats["estado"] = "Inactivo"
                self._emit_to_ui("bot_status", {"running": False, "stats": self.stats})
                self._log_callback("info", "🛑 Hilo de ejecución finalizado.")

        self.bot_thread = threading.Thread(target=run_worker, daemon=True)
        self.bot_thread.start()
        return {"success": True, "message": "Bot iniciado en segundo plano."}

    def stop_bot(self):
        if not self.is_running:
            return {"success": False, "message": "El bot no está en ejecución."}

        self._log_callback("warning", "⏳ Solicitando detención segura del bot...")
        self.stop_event.set()
        self.is_running = False
        self.stats["estado"] = "Deteniendo"
        self._emit_to_ui("bot_status", {"running": False, "stats": self.stats})
        return {"success": True, "message": "Detención solicitada."}

    def get_status(self):
        mat = cargar_materias()
        self.stats["materias_pendientes"] = len(materias_pendientes(mat))
        return {
            "running": self.is_running,
            "stats": self.stats,
            "logs": self.logs_buffer[-50:]
        }
