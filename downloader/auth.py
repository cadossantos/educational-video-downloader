# downloader/auth.py

import time
import pickle
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

def login_and_get_cookies(email, password, save_path=None):
    """Login to Asimov Academy using Selenium and capture cookies"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    
    logger.info("🔑 Iniciando processo de login na Asimov Academy...")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # Access login page
        driver.get("https://hub.asimov.academy/login")

        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))            
        # Fill in login form
        email_field.send_keys(email)
        password_input = driver.find_element(By.ID, "password")
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)
        
        # Wait for login to complete and redirect
        time.sleep(5)
        
        # Check if login was successful
        if "login" in driver.current_url.lower():
            error_msg = driver.find_elements(By.CLASS_NAME, "message-container")
            if error_msg:
                logger.error(f"❌ Falha no login: {error_msg[0].text}")
                driver.quit()
                return False
        
        # Capture cookies
        cookies = driver.get_cookies()
        driver.quit()

        # Format cookies for requests
        cookies = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/112.0",
            "Referer": "https://hub.asimov.academy/",
            "Cookie": cookies
        }
        
        # Save session for future use
        if save_path:
            try:
                with open(save_path, 'wb') as f:
                    pickle.dump({
                        'cookies': cookies,
                        'timestamp': datetime.now()
                    }, f)
                logger.info("💾 Sessão salva com sucesso!")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao salvar sessão: {e}")

        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/112.0",
            "Referer": "https://hub.asimov.academy/",
            "Cookie": cookies
        }

        
        
    except Exception as e:
        logger.error(f"❌ Erro durante o processo de login: {str(e)}")
        return False
