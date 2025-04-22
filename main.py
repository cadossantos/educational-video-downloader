import os
import time
import json
import shutil
import pickle
import requests
import subprocess
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from downloader.utils import sanitize_filename
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm
from markdownify import markdownify as md
from downloader.extract_m3u8 import extract_m3u8_url  # type: ignore
from downloader.auth import login_and_get_cookies
from downloader.parser import extract_iframe_url, extract_lesson_title
from downloader.lessons import process_lesson, process_multiple_lessons, process_course
import logging
from downloader.video_downloader import download_video_with_fallback


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("asimov_downloader.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AsimovDownloader")


class AsimovDownloader:
    def __init__(self, email, password, output_dir="downloads", config_dir=".config", max_retries=3, wait_time=2):
        self.email = email
        self.password = password
        self.cookies = None
        self.headers = None
        self.output_dir = output_dir
        self.config_dir = config_dir
        self.session_file = os.path.join(config_dir, "asimov_session.pkl")
        self.max_retries = max_retries
        self.wait_time = wait_time
        # self.lesson_urls = lesson_urls
        self.process_lesson= process_lesson
        # self.save_lesson_as_markdown= save_lesson_as_markdown
        self.process_multiple_lessons= process_multiple_lessons
        
        # Create necessary directories
        for directory in [output_dir, config_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # Try to load existing session first
        if not self.load_session():
            # If no valid session found, login and get new cookies
            self.headers = login_and_get_cookies(self.email, self.password, save_path=self.session_file)
            self.cookies = self.headers["Cookie"] if self.headers else None
            self.save_session()

    
    def load_session(self):
        """Try to load existing session cookies if they exist and are still valid"""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'rb') as f:
                    session_data = pickle.load(f)
                
                # Check if session is not expired (less than 1 day old)
                if datetime.now() - session_data.get('timestamp', datetime.min) < timedelta(days=1):
                    self.cookies = session_data.get('cookies')
                    self.headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/112.0",
                        "Referer": "https://hub.asimov.academy/",
                        "Cookie": self.cookies
                    }
                    
                    # Test if the session is still valid
                    test_url = "https://hub.asimov.academy/dashboard/"
                    response = requests.get(test_url, headers=self.headers)
                    
                    if "login" not in response.url.lower():
                        logger.info("✅ Sessão existente carregada com sucesso!")
                        logger.debug(f"🍪 Cookies aplicados: {self.cookies}")

                        return True
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar sessão existente: {e}")
        
        logger.info("ℹ️ Nenhuma sessão válida encontrada.")
        return False
    
    def save_session(self):
        """Save current session cookies for future use"""
        session_data = {
            'cookies': self.cookies,
            'timestamp': datetime.now()
        }
        
        with open(self.session_file, 'wb') as f:
            pickle.dump(session_data, f)
        
        logger.info("✅ Sessão salva para uso futuro.")
    
    
    def get_course_page(self, course_url, retry=0):
        """Get course page with retry mechanism"""
        try:
            response = requests.get(course_url, headers=self.headers, timeout=30)
            
            # Check if redirected to login page
            if "login" in response.url.lower() and retry < self.max_retries:
                logger.warning("⚠️ Sessão expirada, tentando novo login...")
                self.headers = login_and_get_cookies(self.email, self.password, save_path=self.session_file)
                self.cookies = self.headers["Cookie"] if self.headers else None
                self.save_session()

                return self.get_course_page(course_url, retry + 1)
                
            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"❌ Erro ao acessar a página: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"❌ Erro na requisição: {str(e)}")
            if retry < self.max_retries:
                wait_time = (retry + 1) * 5  # Exponential backoff
                logger.info(f"⏳ Tentando novamente em {wait_time} segundos...")
                time.sleep(wait_time)
                return self.get_course_page(course_url, retry + 1)
            return None


    def save_lesson_as_markdown(self, lesson_title, lesson_html, prefix=None):
        """Salva o conteúdo da aula como Markdown limpo e com nome numerado"""
        from markdownify import markdownify as md

        if prefix:
            output_filename = f"{prefix}.{lesson_title}.md"
        else:
            output_filename = f"{lesson_title}.md"
            
        output_path = os.path.join(self.output_dir, output_filename)

        try:
            soup = BeautifulSoup(lesson_html, "html.parser")

            # Tenta selecionar o conteúdo da aula (ajustável conforme necessidade)
            content_candidates = [
                soup.select_one("article"),
                soup.select_one("main"),
                soup.select_one(".lesson-content"),
                soup.select_one(".content"),
                soup.body
            ]
            main_content = next((c for c in content_candidates if c), None)

            if not main_content:
                logger.warning("⚠️ Conteúdo principal não encontrado.")
                return False

            # Remove blocos irrelevantes
            for selector in [
                "nav", "aside", "header", "footer", ".sidebar", ".progress",
                ".comentarios", ".comentario", ".comentario-form",
                ".rating", ".anotacao", ".community", ".course-nav", ".google-calendar"
            ]:
                for tag in main_content.select(selector):
                    tag.decompose()

            # Converte HTML para Markdown preservando estrutura
            markdown_text = md(str(main_content), heading_style="ATX")

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# {lesson_title.replace('-', ' ').title()}\n\n")
                f.write(markdown_text.strip())

            logger.info(f"📝 Aula salva em markdown com prefixo: {output_filename}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao salvar markdown: {e}")
            return False


def main():
    # Load credentials from config file if available
    config_file = "config.json"
    email = None
    password = None
    output_dir = "downloads"
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                email = config.get('email')
                password = config.get('password')
                output_dir = config.get('output_dir', 'downloads')
        except Exception as e:
            logger.error(f"❌ Erro ao carregar arquivo de configuração: {str(e)}")
    
    # If credentials not loaded from file, ask user
    if not email or not password:
        email = input("📧 Digite seu e-mail da Asimov Academy: ")
        password = input("🔑 Digite sua senha: ")
        out_dir_input = input("📂 Pasta para salvar os vídeos (padrão: downloads): ")
        if out_dir_input.strip():
            output_dir = out_dir_input
        
        # Ask if user wants to save credentials
        save_config = input("💾 Deseja salvar suas credenciais para uso futuro? (S/N): ").lower() == 's'
        if save_config:
            config = {
                'email': email,
                'password': password,
                'output_dir': output_dir
            }
            try:
                with open(config_file, 'w') as f:
                    json.dump(config, f)
                logger.info("✅ Configurações salvas com sucesso!")
            except Exception as e:
                logger.error(f"❌ Erro ao salvar configurações: {str(e)}")

    # Initialize downloader
    downloader = AsimovDownloader(
        email=email, 
        password=password, 
        output_dir=output_dir,
        max_retries=3,
        wait_time=3,
    )

    shared_args = {
        # "get_course_page": downloader.get_course_page,
        # "save_lesson_as_markdown": downloader.save_lesson_as_markdown,
        "headers": downloader.headers,
        "max_retries": downloader.max_retries,
        "wait_time": downloader.wait_time,
        "output_dir": downloader.output_dir
    }


    while True:
        print("\n" + "="*50)
        print("🎓 Asimov Downloader 2.0")
        print("="*50)
        print("1. Baixar aula específica")
        print("2. Baixar várias aulas")
        print("3. Baixar curso completo")
        print("4. Sair")
        
        choice = input("\n🔢 Escolha uma opção (1-4): ")
        
        if choice == "1":
            lesson_url = input("🔗 Digite a URL da aula: ")
            process_lesson(
                save_lesson_as_markdown=downloader.save_lesson_as_markdown,
                headers=downloader.headers,
                max_retries=downloader.max_retries,
                wait_time=downloader.wait_time,
                output_dir=downloader.output_dir,
                get_course_page=downloader.get_course_page,
                lesson_url=lesson_url,
                prefix="1"
            )

            
        elif choice == "2":
            urls = []
            print("🔗 Digite as URLs das aulas (uma por linha, linha vazia para terminar):")
            while True:
                url = input()
                if not url:
                    break
                urls.append(url)
            
            if urls:
                process_multiple_lessons(
                lesson_urls=urls,
                process_lesson=process_lesson,
                get_course_page=downloader.get_course_page,
                save_lesson_as_markdown=downloader.save_lesson_as_markdown,
                headers=downloader.headers,
                max_retries=downloader.max_retries,
                wait_time=downloader.wait_time,
                output_dir=downloader.output_dir
            )
            else:
                logger.warning("⚠️ Nenhuma URL fornecida.")


                
        elif choice == "3":
            course_url = input("🔗 Digite a URL do curso: ")
            process_course(
            course_url=course_url,
            get_course_page=downloader.get_course_page,
            save_lesson_as_markdown=downloader.save_lesson_as_markdown,
            headers=downloader.headers,
            max_retries=downloader.max_retries,
            wait_time=downloader.wait_time,
            output_dir=downloader.output_dir
        )
            
        elif choice == "4":
            print("👋 Saindo do programa. Até a próxima!")
            break
            
        else:
            print("❌ Opção inválida. Por favor, tente novamente.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Programa interrompido pelo usuário.")
    except Exception as e:
        logger.error(f"\n❌ Erro inesperado: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())