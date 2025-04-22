import os
import time
import re
import shutil
import subprocess
import requests
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)

def download_video_with_fallback(m3u8_url, output_filename, output_dir, headers):
    """Download vídeo, usando diretamente o .m3u8 final quando disponível, ou fallback por qualidade"""
    if not output_filename.endswith('.mp4'):
        output_filename = f"{output_filename}.mp4"
        
    output_path = os.path.join(output_dir, output_filename)
    if os.path.exists(output_path):
        logger.info(f"⏭️ Arquivo já existe: {output_path}")
        return True

    headers = {
        "Referer": "https://iframe.mediadelivery.net/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }

    def baixar_segmentos(m3u8_url_real):
        try:
            r = requests.get(m3u8_url_real, headers=headers)
            if r.status_code != 200:
                return False

            segment_urls = []
            base_url = m3u8_url_real.rsplit('/', 1)[0]
            for line in r.text.splitlines():
                if line.strip().endswith(".ts"):
                    segment_urls.append(f"{base_url}/{line.strip()}")

            if not segment_urls:
                return False

            temp_dir = os.path.join(output_dir, f"temp_{int(time.time())}")
            os.makedirs(temp_dir, exist_ok=True)
            lista_concat = os.path.join(temp_dir, "lista.txt")

            logger.info(f"⬇️ Baixando {len(segment_urls)} segmentos .ts...")
            with open(lista_concat, 'w') as f:
                for i, url in enumerate(tqdm(segment_urls, desc="Downloading segments")):
                    seg_name = f"seg_{i:04d}.ts"
                    seg_path = os.path.join(temp_dir, seg_name)
                    seg_r = requests.get(url, headers=headers)
                    if seg_r.status_code == 200:
                        with open(seg_path, 'wb') as out:
                            out.write(seg_r.content)
                        f.write(f"file '{seg_name}'\n")
                    else:
                        logger.error(f"❌ Erro ao baixar segmento {url}: {seg_r.status_code}")
                        raise Exception("Segmento não encontrado")

            logger.info(f"📦 Concatenando segmentos com ffmpeg...")
            output_temp = f"temp_{int(time.time())}.mp4"
            command = [
                'ffmpeg',
                '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', 'lista.txt',
                '-c', 'copy',
                output_temp
            ]

            process = subprocess.run(command, cwd=temp_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if process.returncode == 0:
                shutil.move(os.path.join(temp_dir, output_temp), output_path)
                logger.info(f"✅ Download e concatenação concluídos: {output_path}")
                shutil.rmtree(temp_dir)
                return True
            else:
                logger.error(f"❌ Erro ao concatenar: {process.stderr.decode()}")
                shutil.rmtree(temp_dir)
                return False

        except Exception as e:
            logger.error(f"❌ Falha no download ou concatenação: {str(e)}")
            return False

    # 1. Tenta baixar direto do .m3u8 recebido
    if baixar_segmentos(m3u8_url):
        return True

    # 2. Fallback para estruturas antigas 1080p/720p
    base_url = m3u8_url.rsplit('/', 1)[0]
    for quality in ["1080p", "720p"]:
        fallback_url = f"{base_url}/{quality}/video.m3u8"
        logger.info(f"⚠️ Tentando fallback: {fallback_url}")
        if baixar_segmentos(fallback_url):
            return True
        else:
            logger.warning(f"⚠️ Qualidade {quality} indisponível, tentando próxima...")

    logger.error("❌ Nenhuma qualidade disponível para download.")
    return False


def download_m3u8_segments(m3u8_url, output_path):
    """
    1. Baixa o .m3u8
    2. Substitui URLs relativas por absolutas
    3. Baixa cada segmento .ts
    4. Concatena com ffmpeg -f concat
    """
    try:
        # Pasta temporária para segmentos
        segment_dir = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(output_path))[0]}_segments")
        if not os.path.exists(segment_dir):
            os.makedirs(segment_dir)
        
        # 1. Baixar o .m3u8
        m3u8_headers = {
            "Referer": "https://hub.asimov.academy/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/112.0",
            "Cookie": cookies
        }
        r = requests.get(m3u8_url, headers=m3u8_headers)
        if r.status_code != 200:
            logger.error(f"❌ Erro ao baixar playlist .m3u8: {r.status_code}")
            return False
        
        playlist_content = r.text.splitlines()
        
        # 2. Ajustar URLs relativas -> absolutas
        base_url = os.path.dirname(m3u8_url)
        absolute_lines = []
        for line in playlist_content:
            if line.startswith("#"):
                # Linha de metadata
                absolute_lines.append(line)
            else:
                # Segmento .ts (ou sub-playlist)
                if not line.startswith("http"):
                    # Converter para URL absoluta
                    line = f"{base_url}/{line}"
                absolute_lines.append(line)
        
        # 3. Baixar cada segmento .ts e gerar lista de concat
        concat_list_path = os.path.join(segment_dir, "file_list.txt")
        with open(concat_list_path, "w", encoding="utf-8") as concat_file:
            segment_index = 0
            for line in absolute_lines:
                if line.startswith("#"):
                    continue
                segment_url = line.strip()
                segment_filename = f"segment_{segment_index}.ts"
                segment_filepath = os.path.join(segment_dir, segment_filename)
                
                # Baixar segmento
                seg_resp = requests.get(segment_url, headers=m3u8_headers, stream=True)
                if seg_resp.status_code == 200:
                    with open(segment_filepath, "wb") as sf:
                        for chunk in seg_resp.iter_content(chunk_size=8192):
                            sf.write(chunk)
                    
                    # Adicionar ao file_list.txt
                    concat_file.write(f"file '{segment_filename}'\n")
                    segment_index += 1
                else:
                    logger.error(f"❌ Erro ao baixar segmento {segment_url}: {seg_resp.status_code}")
                    return False
        
        # 4. Concatena com ffmpeg
        temp_output_path = f"{output_path}.part"
        concat_command = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list_path,
            "-c", "copy",
            temp_output_path
        ]
        
        logger.info(f"📦 Iniciando concatenação de {segment_index} segmentos...")
        concat_proc = subprocess.Popen(concat_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        for line in concat_proc.stderr:
            logger.debug(line.strip())
        concat_proc.wait()
        
        if concat_proc.returncode == 0:
            os.rename(temp_output_path, output_path)
            logger.info(f"✅ Concatenação concluída: {output_path}")
            return True
        else:
            logger.error(f"❌ Erro na concatenação (código {concat_proc.returncode}).")
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)
            return False
        
    except Exception as e:
        logger.error(f"❌ Erro no método manual de download: {e}")
        return False
