# CyberCafé Client

Cliente de escritorio para control de sesiones en cybercafé.

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

Edita `config.py`:
- Cambia `API_BASE_URL` a la URL de tu servidor
- Ajusta `INACTIVITY_MINUTES` (default: 20 min)
- Agrega apps a `APPS_TO_CLOSE` según tu negocio

## Uso

```bash
python main.py
```

## Flujo de la app

1. Abre en **pantalla completa y siempre encima** (no se puede cerrar con Alt+F4)
2. Usuario escribe usuario y contraseña → se valida contra la API
3. Si es correcto → muestra pantalla de sesión activa con:
   - Cronómetro de tiempo de sesión
   - Barra de inactividad (se reinicia con cualquier movimiento de mouse/teclado)
   - Botón de cerrar sesión manual
4. Si pasan 20 min sin actividad → cierra sesión automáticamente
5. Al cerrar sesión:
   - Manda datos a la API (duración, motivo: manual/inactivity)
   - Cierra todas las apps configuradas (Chrome, Firefox, etc.)
   - Vuelve a la pantalla de login

## API esperada

### POST /auth/login
**Body:**
```json
{ "username": "juan", "password": "1234", "pc_name": "PC-01" }
```
**Response 200:**
```json
{ "session_id": "abc123", "username": "juan" }
```
**Response 401:**
```json
{ "detail": "Usuario o contraseña incorrectos" }
```

### POST /sessions/close
**Body:**
```json
{
  "session_id": "abc123",
  "duration_seconds": 3600,
  "logout_reason": "manual",
  "pc_name": "PC-01"
}
```

## Iniciar automáticamente con Windows

1. Presiona `Win + R` → escribe `shell:startup`
2. Crea un acceso directo a `main.py` o crea un `.bat`:

```bat
@echo off
pythonw C:\ruta\a\cybercafe_client\main.py
```
