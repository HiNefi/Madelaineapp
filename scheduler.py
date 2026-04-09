"""
Scheduler: fires at 07:00 and 19:00 Ecuador time (America/Guayaquil, UTC-5).
Picks the oldest unsent message for each slot and sends it via WhatsApp.
"""

import logging

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

log = logging.getLogger(__name__)
ECU = pytz.timezone("America/Guayaquil")


class MessageScheduler:
    def __init__(self, db, wa_sender):
        self.db        = db
        self.wa        = wa_sender
        self._sched    = BackgroundScheduler(timezone=ECU)

        self._sched.add_job(
            self._send_morning,
            CronTrigger(hour=7, minute=0, timezone=ECU),
            id="morning",
            replace_existing=True,
        )
        self._sched.add_job(
            self._send_night,
            CronTrigger(hour=19, minute=0, timezone=ECU),
            id="night",
            replace_existing=True,
        )

    def start(self):
        self._sched.start()
        log.info("Scheduler started – jobs: 07:00 & 19:00 ECU")

    # ------------------------------------------------------------------
    def _dispatch(self, slot: str):
        msg = self.db.get_next_unsent(slot)
        if not msg:
            log.info("No unsent messages for slot %s", slot)
            return
        log.info("Sending msg id=%s slot=%s", msg["id"], slot)
        ok = self.wa.send_message(msg["message"])
        if ok:
            self.db.mark_sent(msg["id"])
        else:
            log.error("Failed to send msg id=%s – will retry next slot", msg["id"])

    def _send_morning(self):
        self._dispatch("7:00 AM")

    def _send_night(self):
        self._dispatch("7:00 PM")
