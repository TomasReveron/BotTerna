# 🤖 BotTerna - Centro de Automatización de Inscripción

Bot avanzado con **Interfaz Gráfica Moderna (PyWebView / Dark Glassmorphic UI)** para la automatización de inscripción en el portal Terna (USM), optimizado para bypass de detecciones y monitoreo ultra-rápido de cupos.

---

## ✨ Características Principales

- **🖥️ Interfaz Gráfica Moderna:** Diseño oscuro premium con estética Glassmorphic (tipo Vercel/Discord), monitoreo de estadísticas en tiempo real y consola integrada.
- **📚 Gestión Visual de Materias y Secciones:** Añade asignaturas y define múltiples secciones con **orden de prioridad visual** (`#1 1MB`, `#2 1MA`, etc.) sin editar archivos JSON manualmente.
- **⚡ Control Total en 1 Clic:** Botones de Iniciar / Detener, selector de modo Headless (ocultar navegador) y prueba de conexión inmediata con Telegram.
- **🛡️ Bypass Anti-Detección:** Basado en `undetected-chromedriver` con perfiles persistentes.
- **🔄 Relogueo Inteligente:** Renovación periódica de sesión para asegurar que la vista de materias esté siempre actualizada.
- **📱 Notificaciones por Telegram:** Alertas instantáneas al abrirse cupos o completarse la inscripción.

---

## 📋 Requisitos Previos

- **Python 3.9+** (Recomendado 3.11 o superior).
- **Google Chrome** instalado en el sistema.

---

## 🛠️ Instalación Rápida

### 1. Clonar o descargar el repositorio
Abre una terminal en la carpeta del proyecto.

### 2. Configurar el Entorno Virtual

**En Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**En Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🚀 Cómo Ejecutar

### Modo Interfaz Gráfica (Recomendado)
Asegúrate de tener el entorno virtual activado y ejecuta:

```bash
python main.py
```
*(O también `python run_gui.py`)*

### Modo Terminal / Consola (CLI)
Si prefieres ejecutar el bot directamente en segundo plano o en un servidor sin entorno gráfico:

```bash
python main.py --cli
```

---

## ⚙️ Configuración

Puedes configurar todo directamente desde la pestaña **Configuración** en la aplicación gráfica, o si lo prefieres, editar el archivo `.env`:

```env
# CREDENCIALES TERNA (Requerido)
USER_UNI=IngresaTuUsuarioAqui
PASS_UNI=IngresaTuClaveAqui

# URLS (Generalmente no cambian)
URL_LOGIN=https://usm.terna.net/
URL_INSCRIPCION=https://usm.terna.net/Inscripcion.php?mid=0

# NOTIFICACIONES TELEGRAM (Opcional)
TOKEN=8460968012:AAHOs7i8kWrg0Y5XNBCGWXU-gOSUzW41zcA
CHAT_ID=TU_CHAT_ID

# MODO HEADLESS (true para ocultar navegador, false para ver la ventana)
HEADLESS=false
```
