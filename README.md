# 💌 Mensajes de Amor

Aplicativo web local / Railway que envía mensajes de amor a tu novia vía **WhatsApp Web** (sin API oficial ni de terceros).

---

## Arquitectura

```
Flask  +  SQLite  +  APScheduler  +  Selenium / Chromium headless
```

| Componente | Descripción |
|---|---|
| `app.py` | Flask – rutas y API JSON |
| `database.py` | SQLite – dos slots de mensajes (7 AM / 7 PM) |
| `scheduler.py` | APScheduler – disparo automático 07:00 y 19:00 ECU |
| `whatsapp_sender.py` | Selenium + Chrome headless → WhatsApp Web |
| `templates/index.html` | SPA minimalista blanco/gris/negro |

---

## Números configurados

| Rol | Número |
|---|---|
| **Envía (tu número)** | +593 97 863 4226 |
| **Recibe (tu novia)** | +593 98 459 5984 |

> El número receptor está en `RECIPIENT_NUMBER` (ver Variables de entorno).

---

## Configuración local

```bash
# 1. Instalar dependencias del sistema (Debian/Ubuntu)
sudo apt install chromium chromium-driver

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias Python
pip install -r requirements.txt

# 4. Ejecutar
python app.py
# → http://localhost:5000
```

---

## Despliegue en Railway

### 1. Crear proyecto
```bash
railway login
railway init
railway up
```

### 2. Variables de entorno (Railway → Variables)

| Variable | Valor |
|---|---|
| `RECIPIENT_NUMBER` | `593984595984` |
| `WA_SESSION_DIR` | `/data/whatsapp_session` |
| `DB_PATH` | `/data/love_messages.db` |
| `CHROME_BIN` | `/usr/bin/chromium` |
| `CHROMEDRIVER_PATH` | `/usr/bin/chromedriver` |

### 3. Volumen persistente (IMPORTANTE)

En Railway → tu servicio → **Volumes** → **New Volume**:
- Mount path: `/data`

Esto mantiene la sesión de WhatsApp y la base de datos entre despliegues.

### 4. Vincular WhatsApp (primera vez)

1. Abre `https://TU-APP.railway.app`
2. Haz clic en **Configurar** (junto al indicador de estado)
3. Verás la pantalla de WhatsApp Web con el código QR
4. En tu teléfono: WhatsApp → **Dispositivos vinculados** → **Vincular dispositivo** → escanea el QR
5. El punto verde confirma la conexión ✓

> La sesión queda guardada en `/data/whatsapp_session`. Solo necesitas escanear una vez mientras el volumen persista.

---

## Uso

### Agregar mensajes
- Botón **Agregar Mensaje** → escribe el texto → elige ☀️ 7 AM o 🌙 7 PM → Guardar

### Ver programados
- **Buenos Días** → muestra mensajes del slot 7 AM con estado ✓/✕
- **Buenas Noches** → ídem para 7 PM

### Enviados
- Los mensajes enviados hace más de 24 h se archivan aquí con fecha y hora exacta

### Envío automático
- Cada día a las **07:00** y **19:00** (hora Ecuador, UTC-5) el scheduler toma el mensaje más antiguo sin enviar y lo manda por WhatsApp

---

## Notas técnicas

- **Un solo worker Gunicorn** es obligatorio para que el singleton de Selenium sobreviva entre requests.
- WhatsApp Web puede cerrar la sesión si la IP del servidor cambia mucho; vuelve a escanear el QR si el punto se pone gris.
- El botón **Enviar Prueba** en el modal de configuración manda un mensaje inmediato para verificar la conexión.
