import os
import sys
import subprocess
import shutil
import argparse


def build(onefile=True):
    print("==================================================")
    print("🔨 BOTTERNA - COMPILADOR A EJECUTABLE AUTÓNOMO")
    print("==================================================")

    # 1. Verificar e instalar PyInstaller si falta
    try:
        import PyInstaller
        print("✅ PyInstaller detectado.")
    except ImportError:
        print("📦 Instalando PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 2. Definir separador de datos según sistema operativo
    # En Windows es ';', en Linux y macOS es ':'
    sep = ";" if os.name == "nt" else ":"
    
    # 3. Comandos de PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=BotTerna",
        "--noconsole",          # Ocultar ventana de consola negra (modo GUI nativo)
        "--clean",              # Limpiar caché de compilaciones anteriores
        "--noconfirm",          # Sobrescribir salida anterior
        f"--add-data=ui{sep}ui",# Incluir carpeta con frontend web
        "--collect-all=pywebview",
        "--collect-all=undetected_chromedriver",
        "--collect-all=PySide6",
    ]

    if onefile:
        cmd.append("--onefile")

    cmd.append("main.py")

    print("\n⚙️  Iniciando proceso de empaquetado (esto puede tardar unos segundos)...")
    print(f"Comando: {' '.join(cmd)}\n")

    result = subprocess.run(cmd)

    if result.returncode == 0:
        exe_suffix = ".exe" if os.name == "nt" else ""
        target = os.path.join(os.path.dirname(__file__), "dist", f"BotTerna{exe_suffix}") if onefile else os.path.join(os.path.dirname(__file__), "dist", "BotTerna")
        print("\n==================================================")
        print("🎉 ¡COMPILACIÓN EXITOSA!")
        print("==================================================")
        print(f"📁 Tu aplicación ejecutable está lista en:")
        print(f"👉 {target}")
        print("==================================================")
    else:
        print("\n❌ Ocurrió un error durante la compilación.")
        sys.exit(result.returncode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--onedir", action="store_true", help="Compilar como carpeta en lugar de archivo único .exe")
    args = parser.parse_args()
    build(onefile=not args.onedir)
