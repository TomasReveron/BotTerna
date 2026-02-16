# BotTerna

Bot de inscripcion con Selenium y notificaciones opcionales por Telegram.

## Requisitos

- Python 3.9+ (recomendado 3.10 o 3.11)
- Google Chrome instalado
- ChromeDriver compatible con tu version de Chrome

## Instalacion (Windows / Linux / macOS)

1) Clona o descarga el proyecto.
2) Crea un entorno virtual e instala dependencias:

Windows (PowerShell):
```
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Linux/macOS (bash/zsh):
```
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## ChromeDriver

- Descarga el ChromeDriver que coincida con tu version de Chrome.
- Ubica el binario en una ruta fija y configuralo en el .env.

Notas:
- En Windows debe terminar en .exe.
- En Linux/macOS el archivo debe ser ejecutable (chmod +x).

## Configuracion (.env)

Crea un archivo .env en la raiz del proyecto con estas variables:

```
# Obligatorias
CHROMEDRIVER_PATH=/ruta/al/chromedriver
URL_LOGIN=https://usm.terna.net/
URL_INSCRIPCION=https://usm.terna.net/Inscripcion.php?mid=0
USER_UNI=tu_usuario
PASS_UNI=tu_password

# Opcionales (Telegram)
TOKEN=tu_token_de_bot
CHAT_ID=tu_chat_id
```

Si no usas Telegram, puedes omitir TOKEN y CHAT_ID.

## materias.json

Define las materias y secciones. Ejemplo:

```
{
  "Matematica I": ["01", "02"],
  "Fisica I": {
    "secciones": ["03"],
    "inscrita": false
  }
}
```

## Ejecutar

Con el entorno activado:

```
python main.py
```

Detener con Ctrl+C.

## Telegram (opcional)

- Envia /status al bot para recibir el estado.
- Asegurate de que TOKEN y CHAT_ID correspondan al mismo chat.

## Problemas comunes

- Error de ChromeDriver: verifica version de Chrome y ruta en CHROMEDRIVER_PATH.
- En Windows: revisa que CHROMEDRIVER_PATH termine en .exe.
- En Linux/macOS: usa chmod +x en el chromedriver si falta permiso.
