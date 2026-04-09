"""
WhatsApp sender using WhatsApp Web + headless Chromium.
No official API or third-party messaging API used.

First run: navigate to /api/whatsapp/qr, scan the QR with
WhatsApp → Dispositivos vinculados → Vincular dispositivo.
The session is saved in WA_SESSION_DIR so you only need to
scan once per Railway volume.
"""

import logging
import os
import time
import urllib.parse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

log = logging.getLogger(__name__)

# ── configuration ──────────────────────────────────────────────────────────
RECIPIENT   = os.environ.get("RECIPIENT_NUMBER", "593984595984")   # no +
SESSION_DIR = os.environ.get("WA_SESSION_DIR",   "/app/whatsapp_session")
CHROME_BIN  = os.environ.get("CHROME_BIN",       "/usr/bin/chromium")
DRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
# ───────────────────────────────────────────────────────────────────────────


class WhatsAppSender:
    """Singleton that keeps one Chromium instance alive for the app lifetime."""

    _instance: "WhatsAppSender | None" = None

    @classmethod
    def get_instance(cls) -> "WhatsAppSender":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    def __init__(self):
        self.driver: webdriver.Chrome | None = None
        self._connected = False
        self._boot()

    # ------------------------------------------------------------------
    def _chrome_options(self) -> Options:
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-software-rasterizer")
        opts.add_argument("--window-size=1400,900")
        opts.add_argument(f"--user-data-dir={SESSION_DIR}")
        if os.path.exists(CHROME_BIN):
            opts.binary_location = CHROME_BIN
        return opts

    def _boot(self):
        os.makedirs(SESSION_DIR, exist_ok=True)
        try:
            opts = self._chrome_options()
            svc  = Service(executable_path=DRIVER_PATH) if os.path.exists(DRIVER_PATH) else Service()
            self.driver = webdriver.Chrome(service=svc, options=opts)
            self.driver.get("https://web.whatsapp.com")
            time.sleep(10)          # give WA Web time to load / restore session
            self._refresh_status()
            log.info("Chrome started. connected=%s", self._connected)
        except Exception as exc:
            log.error("Chrome boot failed: %s", exc)
            self.driver = None

    # ------------------------------------------------------------------
    def _refresh_status(self):
        if not self.driver:
            self._connected = False
            return
        try:
            # If the side-panel exists → logged in
            pane = self.driver.find_elements(By.CSS_SELECTOR, "#pane-side, [data-testid='chatlist']")
            self._connected = bool(pane)
        except Exception:
            self._connected = False

    def is_connected(self) -> bool:
        self._refresh_status()
        return self._connected

    # ------------------------------------------------------------------
    def screenshot_b64(self) -> str | None:
        """Return a PNG screenshot as base-64 (used to show QR in the UI)."""
        if not self.driver:
            return None
        try:
            return self.driver.get_screenshot_as_base64()
        except Exception:
            return None

    # ------------------------------------------------------------------
    def send_message(self, text: str) -> bool:
        """
        Open the wa.me send-URL for the recipient, wait for the send
        button, click it, return True on success.
        """
        if not self.driver:
            log.warning("Driver not available – cannot send.")
            return False
        try:
            encoded = urllib.parse.quote(text)
            url     = f"https://web.whatsapp.com/send?phone={RECIPIENT}&text={encoded}"
            self.driver.get(url)

            wait     = WebDriverWait(self.driver, 40)
            send_btn = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 'button[aria-label="Send"], '
                 'button[data-testid="compose-btn-send"], '
                 'span[data-icon="send"]')
            ))
            send_btn.click()
            time.sleep(3)
            self._connected = True
            log.info("Message sent to %s", RECIPIENT)
            return True
        except Exception as exc:
            log.error("Send failed: %s", exc)
            self._refresh_status()
            return False

    # ------------------------------------------------------------------
    def restart(self):
        """Kill the current browser and start a fresh one."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
        self._connected = False
        self._boot()
