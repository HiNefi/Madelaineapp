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

# Configuración desde variables de entorno
RECIPIENT = os.environ.get("RECIPIENT_NUMBER", "593984595984")
SESSION_DIR = os.environ.get("WA_SESSION_DIR", "./data/whatsapp_session")
CHROME_BIN = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

class WhatsAppSender:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.driver = None
        self._connected = False
        self._boot()

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
            svc = Service(executable_path=CHROMEDRIVER_PATH) if os.path.exists(CHROMEDRIVER_PATH) else Service()
            self.driver = webdriver.Chrome(service=svc, options=opts)
            self.driver.get("https://web.whatsapp.com")
            time.sleep(10)
            self._refresh_status()
            log.info("Chrome started. connected=%s", self._connected)
        except Exception as exc:
            log.error("Chrome boot failed: %s", exc)
            self.driver = None

    def _refresh_status(self):
        if not self.driver:
            self._connected = False
            return
        try:
            pane = self.driver.find_elements(By.CSS_SELECTOR, "#pane-side, [data-testid='chatlist']")
            self._connected = bool(pane)
        except Exception:
            self._connected = False

    def is_connected(self) -> bool:
        self._refresh_status()
        return self._    def send_message(self, text: str) -> bool:
        if not self.driver:
            log.warning("Driver not available – cannot send.")
            return False
        try:
            encoded = urllib.parse.quote(text)
            url = f"https://web.whatsapp.com/send?phone={RECIPIENT}&text={encoded}"
            self.driver.get(url)

            wait = WebDriverWait(self.driver, 40)
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

    def restart(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
        self._connected = False
        self._boot()
