import time
import re
import requests
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

def extract_m3u8_url(iframe_url, headers=None, max_retries=3, wait_time=2):
    """Extrai a melhor URL .m3u8 apontando diretamente para a stream de maior qualidade"""
    logger.debug("🧪 Usando versão modular de extract_m3u8_url()")
    try:
        response = requests.get(iframe_url, headers=headers, timeout=30)

        if response.status_code != 200:
            logger.error(f"❌ Erro ao acessar o iframe: {response.status_code}")
            if max_retries > 0:
                time.sleep(wait_time * (max_retries + 1))
                return extract_m3u8_url(iframe_url, headers, max_retries - 1, wait_time)
            return None

        # Etapa 1: Encontrar a URL do .m3u8 mestre
        m3u8_patterns = [
            r'https://[^"\']+\.m3u8',
            r'"playbackUrl":\s*"([^"]+\.m3u8[^"]*)"',
            r'src="([^"]+\.m3u8[^"]*)"',
            r"src='([^']+\.m3u8[^']*)'",
        ]

        all_matches = set()
        for pattern in m3u8_patterns:
            matches = re.findall(pattern, response.text)
            for url in matches:
                cleaned = url.replace('\\/', '/')
                all_matches.add(cleaned)
                logger.info(f"🎬 URL de vídeo encontrada com padrão: {pattern[:20]}...")

        if not all_matches:
            logger.warning("⚠️ Nenhuma URL .m3u8 encontrada no iframe.")
            return None

        # Etapa 2: Selecionar o .m3u8 com melhor qualidade de stream real
        best_stream = None
        best_quality = 0

        for master_url in all_matches:
            try:
                m3u8_resp = requests.get(master_url, headers=headers, timeout=15)
                base_url = master_url.rsplit("/", 1)[0] + "/"

                for line in m3u8_resp.text.splitlines():
                    match = re.search(r'RESOLUTION=\d+x(\d+)', line)
                    if match:
                        height = int(match.group(1))
                        if height > best_quality:
                            best_quality = height
                    elif best_quality and line.endswith('.m3u8'):
                        # Linha da URL do vídeo (relativa)
                        best_stream = urljoin(base_url, line)

                if best_stream:
                    logger.info(f"✅ Qualidade selecionada: {best_quality}p")
                    return best_stream

            except Exception as e:
                logger.warning(f"⚠️ Falha ao analisar {master_url}: {e}")

        logger.warning("⚠️ Nenhuma stream válida encontrada. Usando primeiro .m3u8 como fallback.")
        return list(all_matches)[0]

    except requests.RequestException as e:
        logger.error(f"❌ Erro na requisição do iframe: {str(e)}")
        if max_retries > 0:
            time.sleep(wait_time * (max_retries + 1))
            return extract_m3u8_url(iframe_url, headers, max_retries - 1, wait_time)
        return None
