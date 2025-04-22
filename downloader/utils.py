import re

def sanitize_filename(filename):
    """Sanitize filename by removing invalid characters and trimming length"""
    # Remove caracteres inválidos
    clean_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    clean_filename = re.sub(r'[\s_]+', '-', clean_filename).strip('-')
    return clean_filename[:200]
