import os
import time
import logging
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from downloader.utils import sanitize_filename
from downloader.parser import extract_iframe_url, extract_lesson_title
from downloader.extract_m3u8 import extract_m3u8_url
from downloader.video_downloader import download_video_with_fallback, download_m3u8_segments
from downloader.auth import login_and_get_cookies

logger = logging.getLogger("AsimovDownloader")


def process_lesson(get_course_page, save_lesson_as_markdown, headers, max_retries, wait_time, output_dir, lesson_url, prefix=None):
    """Processa uma aula individual"""
    logger.info(f"\n🔍 Processando aula: {lesson_url}")
    
    lesson_page = get_course_page(lesson_url)
    if not lesson_page:
        logger.error("❌ Não foi possível obter a página da aula.")
        return False
    
    lesson_title = extract_lesson_title(lesson_page, lesson_url)
    logger.info(f"📌 Título da aula: {lesson_title}")
    
    iframe_url = extract_iframe_url(lesson_page)
    if not iframe_url:
        logger.warning("⚠️ Aula sem vídeo. Tentando salvar conteúdo como markdown...")
        return save_lesson_as_markdown(lesson_title, lesson_page)


    m3u8_url = extract_m3u8_url(
        iframe_url,
        headers=headers,
        max_retries=max_retries,
        wait_time=wait_time
    )

    if not m3u8_url:
        logger.error("❌ URL do m3u8 não encontrada.")
        return False

    # Prefixo numérico, se fornecido
    if prefix is not None:
        output_filename = f"{prefix}.{lesson_title}.mp4"
    else:
        output_filename = f"{lesson_title}.mp4"
    
    success = download_video_with_fallback(
        m3u8_url,
        output_filename,
        output_dir,
        headers=headers
    )

    if not success:
        logger.info("⚠️ Tentando método alternativo de download (manual)")
        return download_m3u8_segments(
            m3u8_url=m3u8_url,
            output_path=os.path.join(output_dir, output_filename),
            headers=headers
        )

    return True


def process_multiple_lessons(
    lesson_urls,
    process_lesson,
    get_course_page,
    save_lesson_as_markdown,
    headers,
    max_retries,
    wait_time,
    output_dir
):
    """Process multiple lessons with progress tracking"""
    total_lessons = len(lesson_urls)
    logger.info(f"\n🚀 Iniciando processamento de {total_lessons} aulas...\n")
    
    success_count = 0
    failed_urls = []
    
    current_index = 1

    for lesson_url in lesson_urls:
        logger.info(f"\n📊 Tentando baixar: {lesson_url}")
        
        success = process_lesson(
            get_course_page=get_course_page,
            save_lesson_as_markdown=save_lesson_as_markdown,
            headers=headers,
            max_retries=max_retries,
            wait_time=wait_time,
            output_dir=output_dir,
            lesson_url=lesson_url,
            prefix=f"{current_index:02d}"
        )
        
        if success:
            success_count += 1
            current_index += 1
        else:
            failed_urls.append(lesson_url)

        
        # Wait between requests to avoid triggering anti-bot measures
        if lesson_url != lesson_urls[-1]:
            logger.info(f"⏳ Aguardando {wait_time} segundos antes da próxima aula...")
            time.sleep(wait_time)
    
    # Report results
    logger.info(f"\n✅ Download concluído! {success_count}/{total_lessons} aulas baixadas com sucesso.")
    
    # Report failed downloads if any
    if failed_urls:
        logger.warning("\n⚠️ As seguintes aulas não puderam ser baixadas:")
        for url in failed_urls:
            logger.warning(f"  - {url}")


def process_course(course_url, get_course_page, save_lesson_as_markdown, headers, max_retries, wait_time, output_dir):
    """Process all lessons in a course"""
    logger.info(f"\n📚 Processando curso: {course_url}")
    
    course_page = get_course_page(course_url)
    logger.debug(course_page[:1000])
    if not course_page:
        logger.error("❌ Não foi possível obter a página do curso.")
        logger.debug(course_page[:1000])
        return False
    
    soup = BeautifulSoup(course_page, 'html.parser')
    
    course_title_elem = soup.select_one('h1') or soup.select_one('.course-title') or soup.select_one('title')
    course_title = sanitize_filename(course_title_elem.text.strip()) if course_title_elem else "Curso"
    
    course_dir = os.path.join(output_dir, course_title)
    os.makedirs(course_dir, exist_ok=True)

    # Detectar todas as aulas
    lesson_links = []
    link_patterns = [
        'div.lessons-wrapper a[href*="/curso/atividade/"]',
        'a.lesson-title', 
        'a.tutor-course-content-list-item-title',
        '.tutor-course-content-list-item a',
        '.course-curriculum a[href*="atividade"]',
        '.course-curriculum a[href*="aula"]',
        '.course-curriculum a[href*="lesson"]',
        'a[href*="atividade"]',
        'a[href*="aula"]',
        'a[href*="lesson"]'
    ]
    
    for pattern in link_patterns:
        links = soup.select(pattern)
        if links:
            lesson_links.extend(links)
            logger.info(f"🔍 Encontrados {len(links)} links com o padrão: {pattern}")
    
    # Normalizar URLs
    lesson_urls = []
    for link in lesson_links:
        if 'href' in link.attrs:
            url = link['href']
            if not url.startswith('http'):
                url = f"https://hub.asimov.academy{url}" if url.startswith('/') else f"https://hub.asimov.academy/{url}"
            if url not in lesson_urls:
                lesson_urls.append(url)
    
    if lesson_urls:
        logger.info(f"📋 Encontradas {len(lesson_urls)} aulas para download")
        process_multiple_lessons(
            process_lesson=process_lesson,
            lesson_urls=lesson_urls,
            get_course_page=get_course_page,
            save_lesson_as_markdown=save_lesson_as_markdown,
            headers=headers,
            max_retries=max_retries,
            wait_time=wait_time,
            output_dir=course_dir
        )
    else:
        logger.warning("⚠️ Nenhuma aula encontrada neste curso.")
        logger.debug(course_page[:1000])
    
    return True
