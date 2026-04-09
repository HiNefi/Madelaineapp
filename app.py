"""
Flask entry-point for Mensajes de Amor.
Starts the scheduler and exposes a JSON API consumed by the SPA front-end.
"""

import logging
import os

from flask import Flask, jsonify, render_template, request

from database import Database
from scheduler import MessageScheduler
from whatsapp_sender import WhatsAppSender

# ── logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
)
log = logging.getLogger(__name__)

# ── app setup ──────────────────────────────────────────────────────────────
app = Flask(__name__)

db        = Database()
wa_sender = WhatsAppSender()
scheduler = MessageScheduler(db, wa_sender)
scheduler.start()


# ══════════════════════════════════════════════════════════════════════════
# Views
# ══════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


# ══════════════════════════════════════════════════════════════════════════
# Messages API
# ══════════════════════════════════════════════════════════════════════════

@app.route("/api/messages/morning")
def api_morning():
    return jsonify(db.get_active_messages("7:00 AM"))


@app.route("/api/messages/night")
def api_night():
    return jsonify(db.get_active_messages("7:00 PM"))


@app.route("/api/messages/sent")
def api_sent():
    return jsonify(db.get_sent_messages())


@app.route("/api/messages", methods=["POST"])
def api_add():
    data          = request.get_json(force=True) or {}
    message       = (data.get("message") or "").strip()
    schedule_time = data.get("schedule_time", "")

    if not message:
        return jsonify({"error": "El mensaje no puede estar vacío."}), 400
    if schedule_time not in ("7:00 AM", "7:00 PM"):
        return jsonify({"error": "Horario inválido."}), 400

    db.add_message(message, schedule_time)
    return jsonify({"success": True})


@app.route("/api/messages/<int:msg_id>", methods=["DELETE"])
def api_delete(msg_id: int):
    db.delete_message(msg_id)
    return jsonify({"success": True})


# ══════════════════════════════════════════════════════════════════════════
# WhatsApp API
# ══════════════════════════════════════════════════════════════════════════

@app.route("/api/whatsapp/status")
def api_wa_status():
    return jsonify({"connected": wa_sender.is_connected()})


@app.route("/api/whatsapp/qr")
def api_wa_qr():
    return jsonify({"screenshot": wa_sender.screenshot_b64()})


@app.route("/api/whatsapp/restart", methods=["POST"])
def api_wa_restart():
    wa_sender.restart()
    return jsonify({"success": True, "connected": wa_sender.is_connected()})


@app.route("/api/whatsapp/test", methods=["POST"])
def api_wa_test():
    data    = request.get_json(force=True) or {}
    message = data.get("message", "¡Hola mi amor! 💕 Mensaje de prueba.")
    ok      = wa_sender.send_message(message)
    return jsonify({"success": ok})


# ══════════════════════════════════════════════════════════════════════════
# Run
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
