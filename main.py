import os
import sys

# Configurar codificación UTF-8 para evitar errores de Unicode/emojis en Windows (cp1252)
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

# Configurar locale UTF-8 para evitar advertencias de Qt en Linux
if "LANG" not in os.environ or "UTF-8" not in os.environ.get("LANG", ""):
    os.environ["LANG"] = "C.UTF-8"
if "LC_ALL" not in os.environ or "UTF-8" not in os.environ.get("LC_ALL", ""):
    os.environ["LC_ALL"] = "C.UTF-8"

os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.locale.warning=false")

# Configurar stdout y stderr para evitar fallos de codificación (ej. emojis en Windows cp1252) o en modo --noconsole
def _configurar_salida_consola():
    if sys.stdout is None:
        try:
            sys.stdout = open(os.devnull, "w", encoding="utf-8", errors="replace")
        except Exception:
            pass
    elif hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    elif hasattr(sys.stdout, "buffer"):
        import io
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        except Exception:
            pass

    if sys.stderr is None:
        try:
            sys.stderr = open(os.devnull, "w", encoding="utf-8", errors="replace")
        except Exception:
            pass
    elif hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    elif hasattr(sys.stderr, "buffer"):
        import io
        try:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
        except Exception:
            pass

_configurar_salida_consola()

from time import sleep
from bot import iniciar_bot
from materias_store import cargar_materias, materias_pendientes


def ejecutar_cli():
    try:
        materias = cargar_materias()
        if len(materias_pendientes(materias)) == 0:
            print("🎉 Todas las materias ya están marcadas como inscritas en materias.json.")
            print("Si deseas volver a inscribir, edita materias.json y coloca 'inscrita': false.")
            raise SystemExit(0)

        while True:
            exito = iniciar_bot()
            if exito:
                print("\n✅ Proceso completado: Todas las materias fueron inscritas con éxito.")
                break
            
            materias_actuales = cargar_materias()
            if len(materias_pendientes(materias_actuales)) == 0:
                print("\n✅ No quedan materias pendientes por inscribir.")
                break

            print("\n🔄 Reiniciando bot en 3 segundos...")
            sleep(3)

    except KeyboardInterrupt:
        print("\n🛑 Programa finalizado por el usuario.")


if __name__ == "__main__":
    if "--cli" in sys.argv:
        ejecutar_cli()
    else:
        try:
            from run_gui import main as ejecutar_gui
            ejecutar_gui()
        except ImportError as e:
            print(f"⚠️  No se pudo cargar la interfaz gráfica ({e}). Ejecutando en modo consola...")
            ejecutar_cli()