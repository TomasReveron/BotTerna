import json
import os
import ssl
import urllib.parse
import urllib.request
from threading import Event, Lock, Thread
from time import sleep

try:
    import certifi
except Exception:
    certifi = None


def _crear_contexto_ssl():
    if certifi:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


DEFAULT_TELEGRAM_TOKEN = "8460968012:AAHOs7i8kWrg0Y5XNBCGWXU-gOSUzW41zcA"


def tiene_webhook_activo():
    """Verifica si hay un webhook activo en Telegram."""
    token = os.getenv("TOKEN") or DEFAULT_TELEGRAM_TOKEN
    if not token:
        return False

    url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    ssl_context = _crear_contexto_ssl()
    try:
        with urllib.request.urlopen(url, timeout=10, context=ssl_context) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                result = data.get("result", {})
                webhook_url = result.get("url", "")
                if webhook_url:
                    return True
    except Exception as e:
        print(f"⚠️  Error verificando webhook: {e}")
    
    return False


def enviar_telegram(mensaje):
    token = os.getenv("TOKEN") or DEFAULT_TELEGRAM_TOKEN
    chat_id = os.getenv("CHAT_ID")

    if not chat_id:
        return

    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": mensaje}).encode("utf-8")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    ssl_context = _crear_contexto_ssl()

    try:
        with urllib.request.urlopen(url, data=payload, timeout=10, context=ssl_context) as response:
            if response.status != 200:
                print(f"⚠️  Error Telegram: HTTP {response.status}")
    except Exception as e:
        # Silenciamos errores comunes de red que son transitorios
        error_msg = str(e)
        if "104" in error_msg or "Connection reset" in error_msg:
            # Reintentar una vez tras un pequeño sleep
            sleep(1)
            try:
                with urllib.request.urlopen(url, data=payload, timeout=10, context=ssl_context) as response:
                    pass
            except Exception:
                pass
        else:
            print(f"⚠️  Error enviando Telegram: {e}")


def telegram_habilitado():
    return bool(os.getenv("TOKEN") and os.getenv("CHAT_ID"))


def obtener_actualizaciones(offset):
    token = os.getenv("TOKEN")
    if not token:
        return [], offset

    # Usamos timeout=20 para Long-Polling eficiente
    params = urllib.parse.urlencode({"timeout": 20, "offset": offset})
    url = f"https://api.telegram.org/bot{token}/getUpdates?{params}"
    ssl_context = _crear_contexto_ssl()

    try:
        with urllib.request.urlopen(url, timeout=25, context=ssl_context) as response:
            if response.status != 200:
                return [], offset
            payload = json.loads(response.read().decode("utf-8"))
            return payload.get("result", []), offset
    except Exception as e:
        error_msg = str(e)
        if "104" in error_msg or "Connection reset" in error_msg or "timed out" in error_msg:
            # Parpadeo de red o timeout normal de long polling
            pass
        elif "409" in error_msg:
            print("⚠️  Conflicto de Telegram (409): Hay un Webhook activo u otra instancia del bot corriendo.")
            sleep(5)
        else:
            print(f"⚠️  Error leyendo comandos de Telegram: {e}")
        return [], offset


def hilo_telegram(stop_event, estado_ref, estado_lock):
    """Hilo principal para escuchar comandos de Telegram."""
    
    if tiene_webhook_activo():
        print("ℹ️  Webhook de Telegram detectado activo.")
        print("⚠️  El bot SOLO enviará notificaciones, NO escuchará comandos (para no interferir con el otro bot).")
        return

    offset = 0
    while not stop_event.is_set():
        # Leer estado actual
        with estado_lock:
            estado = estado_ref.get("texto", "Estado: iniciando")

        # Procesar actualizaciones
        try:
            offset = procesar_comandos_telegram(offset, estado)
        except Exception as e:
            print(f"⚠️  Error en hilo Telegram: {e}")
        
        sleep(3)


def procesar_comandos_telegram(offset, estado):
    if not telegram_habilitado():
        return offset

    updates, offset = obtener_actualizaciones(offset)

    if not updates:
        return offset

    chat_id = os.getenv("CHAT_ID")

    for update in updates:
        update_id = update.get("update_id")
        if update_id is not None:
            # Siempre avanzamos el offset para no leer el mismo mensaje eternamente
            if update_id >= offset:
                offset = update_id + 1

        message = update.get("message") or {}
        text = (message.get("text") or "").strip()
        
        # Validación de chat_id más robusta (str vs int)
        from_chat = message.get("chat", {}).get("id")
        if str(from_chat) != str(chat_id):
            continue

        if text == "/status":
            enviar_telegram(estado)

    return offset


def iniciar_hilo_telegram(estado_ref, estado_lock):
    stop_event = Event()
    hilo = None

    if telegram_habilitado():
        hilo = Thread(
            target=hilo_telegram,
            args=(stop_event, estado_ref, estado_lock),
            daemon=True
        )
        hilo.start()

    return stop_event, hilo
