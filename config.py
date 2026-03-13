# ─── CONFIGURACIÓN DEL CLIENTE CYBERCAFÉ ─────────────────────────────────────
# Edita este archivo para personalizar el cliente

# ⚠️  MODO DESARROLLO
# True  → ventana normal, Alt+F4 funciona, login sin API
# False → fullscreen real, bloqueado, requiere API
DEV_MODE = True

# URL de tu API backend
API_BASE_URL = "http://localhost:8000"

# Minutos de inactividad antes de cerrar sesión automáticamente
INACTIVITY_MINUTES = 1

# Nombre de esta PC (se detecta automáticamente, pero puedes forzar uno)
# PC_NAME = "PC-01"   # descomenta para forzar un nombre

# Aplicaciones a cerrar al terminar la sesión
# Agrega o quita según lo que uses en tu cybercafé
APPS_TO_CLOSE = [
    "chrome.exe",
    "msedge.exe",
    "firefox.exe",
    "opera.exe",
    "brave.exe",
    "notepad.exe",
    "wordpad.exe",
    "mspaint.exe",
    "vlc.exe",
    "winword.exe",
    "excel.exe",
    "powerpnt.exe",
    "discord.exe",
    "telegram.exe",
    "whatsapp.exe",
    "spotify.exe",
    "steam.exe",
]