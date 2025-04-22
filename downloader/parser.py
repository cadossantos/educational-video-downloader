import time
import re
from bs4 import BeautifulSoup
import logging
from downloader.utils import sanitize_filename

logger = logging.getLogger(__name__)

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


def extract_iframe_url(lesson_page):
    """Extract iframe URL where the video is embedded"""
    soup = BeautifulSoup(lesson_page, 'html.parser')
    
    # Try different patterns for iframe (some courses use different players)
    iframe_patterns = [
        {"src": re.compile(r'https://iframe\.mediadelivery\.net/')},
        {"src": re.compile(r'https://player\.vimeo\.com/')},
        {"src": re.compile(r'https://www\.youtube\.com/embed/')},
        {"src": re.compile(r'https://bunny\.cdn\.net/')},
        {"class": "bunny-video"}
    ]
    
    for pattern in iframe_patterns:
        iframe = soup.find("iframe", pattern)
        if iframe and "src" in iframe.attrs:
            logger.info(f"🔍 Tipo de iframe encontrado: {pattern}")
            return iframe["src"]
    
    # Look for other video containers if iframe not found
    video_element = soup.find("video", {"src": True})
    if video_element:
        logger.info("🔍 Elemento <video> encontrado diretamente")
        return video_element["src"]
        
    # Try to find any data attributes that might contain video URLs
    video_containers = soup.select("[data-src], [data-video-url], [data-video-id]")
    for container in video_containers:
        for attr in ["data-src", "data-video-url", "data-video-id"]:
            if container.has_attr(attr) and container[attr]:
                logger.info(f"🔍 Atributo de vídeo encontrado: {attr}")
                return container[attr]
    
    logger.warning("⚠️ Não foi possível encontrar o iframe do vídeo.")
    return None

def extract_lesson_title(lesson_page, lesson_url=None):
    """Extrai o título da aula com base na URL"""
    if lesson_url:
        url_parts = lesson_url.rstrip('/').split('/')
        last_part = url_parts[-1]
        if last_part and last_part != "assistir":
            return sanitize_filename(last_part)

    # Fallback final
    return f"aula_{int(time.time())}"