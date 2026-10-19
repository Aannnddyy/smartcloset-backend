import io
import json
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from PIL import Image
from rembg import remove


def remove_background_and_crop(image_field, max_size=(800, 800)) -> ContentFile:
    """
    Recibe un archivo de imagen, reduce su resolución máxima con Pillow para acelerar
    el procesamiento, elimina el fondo con rembg, recorta el espacio transparente sobrante
    y devuelve un ContentFile en formato PNG transparente.
    """
    if hasattr(image_field, 'open'):
        image_field.open()

    image_field.seek(0)

    # 1. Reducción previa de escala para evitar bloqueos y timeouts de CPU
    img = Image.open(image_field)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    temp_buffer = io.BytesIO()
    img.save(temp_buffer, format="PNG")
    temp_buffer.seek(0)

    # 2. Eliminación de fondo con rembg
    output_bytes = remove(temp_buffer.getvalue())

    # 3. Recorte automático del espacio transparente sobrante
    processed_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
    bounding_box = processed_img.getbbox()
    if bounding_box:
        processed_img = processed_img.crop(bounding_box)

    # 4. Generación del ContentFile final
    final_buffer = io.BytesIO()
    processed_img.save(final_buffer, format="PNG", optimize=True)
    final_buffer.seek(0)

    original_name = image_field.name.split('/')[-1].split('.')[0]
    filename = f"processed_{original_name}.png"
    return ContentFile(final_buffer.getvalue(), name=filename)


def extract_image_from_url(target_url: str) -> ContentFile:
    """
    Descarga una imagen tanto si se pasa la URL directa del archivo (o CDN como Zara)
    como si se pasa el enlace de una tienda estándar con etiquetas OpenGraph/Twitter Cards/JSON-LD.
    """
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        ),
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    }

    parsed = urlparse(target_url)
    clean_path = parsed.path.lower()
    
    # Comprobación de si es enlace directo o CDN estático
    is_direct_image = (
        any(clean_path.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.avif'])
        or 'static.zara.net' in parsed.netloc
    )

    image_url = target_url if is_direct_image else None

    # Si es una página web tradicional, parseamos el HTML
    if not image_url:
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Metadatos OpenGraph / Twitter Cards
        og_image = (
            soup.find('meta', property='og:image')
            or soup.find('meta', property='og:image:secure_url')
            or soup.find('meta', attrs={'name': 'twitter:image'})
            or soup.find('meta', attrs={'name': 'twitter:image:src'})
            or soup.find('link', rel='image_src')
        )

        if og_image:
            image_url = og_image.get('content') or og_image.get('href')

        # 2. Fallback a Schema.org / JSON-LD
        if not image_url:
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string or '')
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if 'image' in item:
                            img = item['image']
                            image_url = img if isinstance(img, str) else (img[0] if isinstance(img, list) else None)
                            if image_url:
                                break
                    if image_url:
                        break
                except (json.JSONDecodeError, TypeError):
                    continue

    if not image_url:
        raise ValueError("No se pudo obtener la imagen del enlace facilitado.")

    # Descarga del archivo binario
    img_response = requests.get(image_url, headers=headers, timeout=12)
    img_response.raise_for_status()

    clean_img_path = urlparse(image_url).path
    filename = clean_img_path.split('/')[-1]
    if not filename or '.' not in filename:
        filename = "imported_item.jpg"

    return ContentFile(img_response.content, name=filename)