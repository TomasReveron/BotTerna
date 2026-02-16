import json
import os
import urllib.parse
import urllib.request
from threading import Event, Lock, Thread
from time import sleep


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
