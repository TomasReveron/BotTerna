# 🤖 BotTerna - Automatización de Inscripción

Bot avanzado para la automatización de inscripción en Terna (USM), optimizado para evitar detecciones y agilizar el proceso de captura de cupos.

---

## 📋 Requisitos Previos

- **Python 3.9+** (Recomendado 3.11).
- **Google Chrome** instalado en su versión más reciente.
- **ChromeDriver**: Compatible con tu versión de Chrome.
- **Telegram (Opcional)**: Un bot creado vía `@BotFather` si deseas recibir notificaciones.

---

## 🛠️ Instalación Paso a Paso

### 1. Preparación del Proyecto
Clona el repositorio o descarga los archivos en una carpeta local.

### 2. Configuración del Entorno Virtual (Recomendado)
Abre una terminal en la carpeta del proyecto y ejecuta:

**En Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**En Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configuración del Driver (Opcional)
- El bot gestiona y descarga automáticamente el ChromeDriver compatible con tu versión de Google Chrome tanto en Windows como en Linux/macOS.
- Si prefieres usar un binario manual, coloca el archivo `chromedriver` (o `chromedriver.exe` en Windows) en la carpeta del proyecto y especifica su ruta en el `.env`.

---

## ⚙️ Configuración del Bot (`.env`)

Crea un archivo llamado `.env` en la raíz del proyecto y completa los siguientes datos:

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

# RUTA DEL DRIVER (Opcional - Si lo omites, se descargará automáticamente)
# CHROMEDRIVER_PATH=./chromedriver.exe   (En Windows)
# CHROMEDRIVER_PATH=./chromedriver       (En Linux)

```

---

## 📚 Configuración de Materias (`materias.json`)

Edita el archivo `materias.json` para definir qué materias quieres inscribir y en qué secciones.

**Formato:**
```json
{
  "NOMBRE DE LA MATERIA": {
    "secciones": ["SECCION (1MA)"],
    "inscrita": false
  }
}
```
*El bot solo intentará inscribir aquellas donde `"inscrita"` sea `false`.*

---

## 🚀 Cómo Ejecutar

Asegúrate de tener el entorno virtual activado y ejecuta:

```bash
python main.py
```

### Características del Bot:
- **Bypass de Seguridad:** Utiliza `undetected-chromedriver` para evitar bloqueos.
- **Relogueo Automático:** Cada ciclo de espera realiza un logout/login completo para mantener la sesión fresca.
- **Detección Inteligente:** Solo intenta inscribir si detecta que hay cupos disponibles (formato `SECCIÓN:CUPOS > 0`).
- **Notificaciones:** Te avisa por Telegram apenas las materias aparecen o se inscriben con éxito.

---

## ❓ Solución de Problemas

- **Error de Conector:** Asegúrate de que la ruta en `CHROMEDRIVER_PATH` sea absoluta o relativa correcta y que el archivo tenga permisos.
- **Detección de Bot:** El bot usa técnicas de sigilo, pero si Terna muestra un Captcha, el navegador se detendrá unos segundos para permitirte cargarlo (o puedes ajustar el `sleep` en `bot.py`).
- **Cierre Inesperado:** Revisa que tus credenciales en el `.env` sean correctas.
