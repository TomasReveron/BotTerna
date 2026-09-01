import hashlib
import json
import os
import platform
import uuid
import requests
from config import obtener_ruta_base

# URL por defecto de la API de Google Apps Script
# Se puede sobreescribir mediante la variable de entorno GOOGLE_SCRIPT_URL en .env
DEFAULT_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwIpq7hc02n2AuQESKd07G9F7bc66dBuH1dHyDS2nfPYU4Ha5nVkQ7v925kP2P3nvf2hw/exec"


def obtener_hardware_id() -> str:
    """
    Genera un identificador de hardware único y determinista para la máquina actual.
    """
    raw_id = ""
    system_name = platform.system()

    if system_name == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
            raw_id, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
        except Exception:
            pass

    elif system_name == "Linux":
        if os.path.exists("/etc/machine-id"):
            try:
                with open("/etc/machine-id", "r") as f:
                    raw_id = f.read().strip()
            except Exception:
                pass
        elif os.path.exists("/var/lib/dbus/machine-id"):
            try:
                with open("/var/lib/dbus/machine-id", "r") as f:
                    raw_id = f.read().strip()
            except Exception:
                pass

    elif system_name == "Darwin":  # macOS
        try:
            import subprocess
            out = subprocess.check_output(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]).decode("utf-8")
            for line in out.splitlines():
                if "IOPlatformUUID" in line:
                    raw_id = line.split("=")[1].strip().strip('"')
                    break
        except Exception:
            pass

    # Fallback universal si no se pudo leer el ID del sistema
    if not raw_id:
        raw_id = f"{uuid.getnode()}_{platform.node()}_{platform.processor()}"

    # Hash SHA-256 formateado como código limpio
    hash_hex = hashlib.sha256(f"BOTTERNA_HWID_SALT_{raw_id}".encode("utf-8")).hexdigest().upper()
    return f"HWID-{hash_hex[:4]}-{hash_hex[4:8]}-{hash_hex[8:12]}"


def obtener_ruta_licencia() -> str:
    """Devuelve la ruta absoluta al archivo license.json persistente."""
    return os.path.join(obtener_ruta_base(estatico=False), "license.json")


def obtener_script_url() -> str:
    """Obtiene la URL de Google Apps Script desde el archivo .env o configuración."""
    from config import cargar_env_local
    cargar_env_local()
    return os.getenv("GOOGLE_SCRIPT_URL") or os.getenv("LICENSE_API_URL") or DEFAULT_SCRIPT_URL


def leer_licencia_local() -> dict:
    """Lee la licencia guardada localmente si existe."""
    ruta = obtener_ruta_licencia()
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def guardar_licencia_local(data: dict) -> None:
    """Guarda la licencia localmente."""
    ruta = obtener_ruta_licencia()
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error guardando licencia local: {e}")


def validar_licencia_en_nube(key: str, hwid: str, script_url: str = None) -> dict:
    """
    Realiza la petición a Google Apps Script para validar o activar una clave.
    """
    url = script_url or obtener_script_url()

    if not url:
        # Si no hay URL configurada aún, permitimos modo local si existe clave
        return {
            "success": True,
            "message": "Licencia local verificada.",
            "cliente": "Usuario Local",
            "offline_mode": True
        }

    payload = {
        "action": "validate",
        "key": key.strip().upper(),
        "hwid": hwid.strip()
    }

    try:
        # Seguir redirecciones de Google Apps Script (302)
        response = requests.post(url, json=payload, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            try:
                return response.json()
            except Exception:
                # Si Google devuelve texto plano o redirect content
                return {"success": False, "message": "Respuesta no válida de Google Apps Script."}
        else:
            return {"success": False, "message": f"Error del servidor Google ({response.status_code})."}
    except requests.exceptions.Timeout:
        return {"success": False, "message": "Tiempo de espera agotado al conectar con Google Sheets."}
    except Exception as e:
        return {"success": False, "message": f"No se pudo conectar con el servidor: {str(e)}"}


def verificar_estado_licencia() -> dict:
    """
    Comprueba si la app tiene una licencia activa y válida.
    """
    hwid = obtener_hardware_id()
    lic_local = leer_licencia_local()
    key = lic_local.get("key", "").strip()

    if not key:
        return {
            "active": False,
            "hwid": hwid,
            "message": "Se requiere una clave de activación para usar BotTerna."
        }

    script_url = obtener_script_url()
    res = validar_licencia_en_nube(key, hwid, script_url)

    if res.get("success"):
        lic_local["hwid"] = hwid
        lic_local["cliente"] = res.get("cliente", "Usuario")
        lic_local["active"] = True
        guardar_licencia_local(lic_local)
        return {
            "active": True,
            "key": key,
            "hwid": hwid,
            "cliente": res.get("cliente", "Usuario"),
            "message": res.get("message", "Licencia válida.")
        }
    else:
        # Invalidar archivo local si la clave fue revocada, modificada o eliminada en Google Sheets
        ruta_lic = obtener_ruta_licencia()
        if os.path.exists(ruta_lic):
            try:
                os.remove(ruta_lic)
            except Exception:
                pass
        return {
            "active": False,
            "key": key,
            "hwid": hwid,
            "message": res.get("message", "Esta licencia fue invalidada o revocada por el administrador.")
        }


def activar_clave_licencia(key: str) -> dict:
    """
    Intenta activar una nueva clave ingresada por el usuario.
    """
    key_clean = (key or "").strip().upper()
    if not key_clean:
        return {"success": False, "message": "Ingresa una clave de activación válida."}

    hwid = obtener_hardware_id()
    res = validar_licencia_en_nube(key_clean, hwid)

    if res.get("success"):
        data_to_save = {
            "key": key_clean,
            "hwid": hwid,
            "cliente": res.get("cliente", "Usuario"),
            "active": True
        }
        guardar_licencia_local(data_to_save)
        return {
            "success": True,
            "message": res.get("message", "¡Licencia activada con éxito!"),
            "cliente": res.get("cliente", "Usuario"),
            "key": key_clean,
            "hwid": hwid
        }
    else:
        return {
            "success": False,
            "message": res.get("message", "Clave no válida o ya utilizada.")
        }
