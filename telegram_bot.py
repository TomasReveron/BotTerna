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


def tiene_webhook_activo():
    """Verifica si hay un webhook activo en Telegram."""
    token = os.getenv("TOKEN")
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
    token = os.getenv("TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token and not chat_id:
        return
    if not token or not chat_id:
        print("⚠️  Faltan TOKEN o CHAT_ID para Telegram.")
        return

    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": mensaje}).encode("utf-8")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    ssl_context = _crear_contexto_ssl()

    try:
        with urllib.request.urlopen(url, data=payload, timeout=10, context=ssl_context) as response:
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

    # Usamos timeout=0 para polling corto o largo según prefieras
    params = urllib.parse.urlencode({"timeout": 0, "offset": offset})
    url = f"https://api.telegram.org/bot{token}/getUpdates?{params}"
    ssl_context = _crear_contexto_ssl()

    try:
        # Usamos GET en lugar de POST con data, a veces es más estable para urllib simple
        with urllib.request.urlopen(url, timeout=10, context=ssl_context) as response:
            if response.status != 200:
                return [], offset
            payload = json.loads(response.read().decode("utf-8"))
            return payload.get("result", []), offset
    except Exception as e:
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
