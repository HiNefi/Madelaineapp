import os
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime

def get_db():
    if not hasattr(get_db, "_instance"):
        from database import Database
        get_db._instance = Database()
    return get_db._instance

app = Flask(__name__, static_folder='templates')

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/messages", methods=["POST"])
def api_add_message():
    data = request.get_json()
    message = data.get("message", "").strip()
    schedule_time = data.get("schedule_time", "")

    if not message:
        return jsonify({"error": "El mensaje no puede estar vacío."}), 400
    if schedule_time not in ("7:00 AM", "7:00 PM"):
        return jsonify({"error": "Horario inválido. Use '7:00 AM' o '7:00 PM'."}), 400

    db = get_db()
    db.add_message(message, schedule_time)
    return jsonify({"success": True})

@app.route("/api/messages/<int:msg_id>", methods=["DELETE"])
def api_delete(msg_id):
    db = get_db()
    db.delete_message(msg_id)
    return jsonify({"success": True})

@app.route("/api/status")
def api_status():
    try:
        from whatsapp_sender import WhatsAppSender
        wa = WhatsAppSender.get_instance()
        return jsonify({"connected": wa.is_connected()})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)}), 500

@app.route("/api/send-test", methods=["POST"])
def api_send_test():
    try:
        from whatsapp_sender import WhatsAppSender
        wa = WhatsAppSender.get_instance()
        if not wa.is_connected():
            return jsonify({"error": "WhatsApp no conectado"}), 400
        success = wa.send_message("✅ Mensaje de prueba desde Railway")
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
