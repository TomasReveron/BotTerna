import os
import sys

# Configurar locale UTF-8 para evitar advertencias de Qt en Linux
if "LANG" not in os.environ or "UTF-8" not in os.environ.get("LANG", ""):
    os.environ["LANG"] = "C.UTF-8"
if "LC_ALL" not in os.environ or "UTF-8" not in os.environ.get("LC_ALL", ""):
    os.environ["LC_ALL"] = "C.UTF-8"

# Silenciar mensajes de diagnóstico redundantes de Qt en la terminal
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.locale.warning=false")

import threading
import http.server
import webview
from config import obtener_ruta_base
from gui_bridge import BotBridgeApi


class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        ui_dir = os.path.join(obtener_ruta_base(estatico=True), "ui")
        super().__init__(*args, directory=ui_dir, **kwargs)

    def log_message(self, format, *args):
        # Silenciar los logs de peticiones HTTP en consola para mantenerla limpia
        pass


def iniciar_servidor_local():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), QuietHTTPHandler)
    puerto = server.server_address[1]
    hilo = threading.Thread(target=server.serve_forever, daemon=True)
    hilo.start()
    return server, puerto


def main():
    api = BotBridgeApi()
    
    ui_dir = os.path.join(obtener_ruta_base(estatico=True), "ui")
    index_html = os.path.join(ui_dir, "index.html")

    if not os.path.exists(index_html):
        print(f"❌ Error: No se encontró el archivo {index_html}")
        sys.exit(1)

    server, puerto = iniciar_servidor_local()
    url_local = f"http://127.0.0.1:{puerto}/index.html"

    window = webview.create_window(
        title="BotTerna - Centro de Control de Inscripción",
        url=url_local,
        js_api=api,
        width=1120,
        height=760,
        min_size=(920, 620),
        background_color="#080c14",
        text_select=True
    )

    api.set_window(window)
    
    print(f"🚀 Interfaz web disponible en: http://localhost:{puerto}/")
    print("🖥️  Lanzando ventana de escritorio...")
    try:
        webview.start(gui="qt", debug=False)
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
