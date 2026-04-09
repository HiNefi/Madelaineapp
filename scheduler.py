import os
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

def get_db():
    if not hasattr(get_db, "_instance"):
        from database import Database
        get_db._instance = Database()
    return get_db._instance

def schedule_daily_tasks():
    scheduler = BackgroundScheduler()
    
    # Ejemplo: disparar a las 7:00 AM y 7:00 PM (hora local del servidor — ajusta si necesitas UTC)
    scheduler.add_job(send_pending_messages, 'cron', hour=7, minute=0, timezone='America/Guayaquil')
    scheduler.add_job(send_pending_messages, 'cron', hour=19, minute=0, timezone='America/Guayaquil')
    
    scheduler.start()
    return scheduler

def send_pending_messages():
    db = get_db()
    # Aquí iría tu lógica para enviar mensajes pendientes
    # Ejemplo:
    # pending = db.get_pending("7:00 AM")  # o "7:00 PM"
    # for msg_id, msg, _, _ in pending:
    #     if WhatsAppSender.get_instance().send_message(msg):
    #         db.mark_as_sent(msg_id)
    pass
