import io
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests
from django.core.files.base import ContentFile
from PIL import Image
from playwright.sync_api import sync_playwright
from rembg import new_session, remove

COMMON_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
}

SESSION_REMBG = new_session(model_name="u2netp")


def remove_background_and_crop(image_field, max_size=(800, 800)) -> ContentFile:
    if hasattr(image_field, 'open'):
        image_field.open()

    image_field.seek(0)
    img = Image.open(image_field)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    temp_buffer = io.BytesIO()
    img.save(temp_buffer, format="PNG")
    temp_buffer.seek(0)

    output_bytes = remove(temp_buffer.getvalue(), session=SESSION_REMBG)

    processed_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
    bounding_box = processed_img.getbbox()
    if bounding_box:
        processed_img = processed_img.crop(bounding_box)

    final_buffer = io.BytesIO()
    processed_img.save(final_buffer, format="PNG", optimize=True)
    final_buffer.seek(0)

    original_name = image_field.name.split('/')[-1].split('.')[0]
    filename = f"processed_{original_name}.png"
    return ContentFile(final_buffer.getvalue(), name=filename)


def download_image_from_url(image_url: str) -> ContentFile:
    response = requests.get(image_url, headers=COMMON_HEADERS, timeout=15)
    response.raise_for_status()

    parsed_path = urlparse(image_url).path
    filename = parsed_path.split('/')[-1]

    if not filename or '.' not in filename:
        filename = "garment_item.jpg"
    elif '?' in filename:
        filename = filename.split('?')[0]

    return ContentFile(response.content, name=filename)


def clean_and_deduplicate_urls(raw_urls: list) -> list:
    unique_images = {}
    width_param_names = ['w', 'wid', 'width', 'imwidth', 'size']

    for url in raw_urls:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        detected_width_param = None
        for wp in width_param_names:
            if wp in params:
                detected_width_param = wp
                break

        if detected_width_param:
            params[detected_width_param] = ['1800']
            clean_query = urlencode(params, doseq=True)
            normalized_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                clean_query,
                parsed.fragment
            ))
        else:
            normalized_url = url

        base_path = parsed.path

        if base_path in unique_images:
            if 'packshot' in normalized_url and 'packshot' not in unique_images[base_path]:
                unique_images[base_path] = normalized_url
        else:
            unique_images[base_path] = normalized_url

    return list(unique_images.values())


def extract_product_preview(product_url: str) -> dict:
    title_hint = ""

    ignored_keywords = [
        'logo', 'icon', 'pixel', 'avatar', 'badge', 'banner',
        'rating', 'star', 'arrow', 'payment', 'footer', 'header',
        'cart', 'bag', 'heart', 'flag', 'chip', 'swatch', 'placeholder'
    ]

    valid_extensions = ['.jpg', '.jpeg', '.webp', '.png', '.avif']

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            channel="chrome",
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )

        context = browser.new_context(
            user_agent=COMMON_HEADERS['User-Agent'],
            locale="es-ES",
            viewport={"width": 1440, "height": 900}
        )

        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            page.goto(product_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)

            page.evaluate("""
                async () => {
                    for (let i = 0; i < 4; i++) {
                        window.scrollBy(0, 800);
                        await new Promise(r => setTimeout(r, 300));
                    }
                }
            """)
            page.wait_for_timeout(1000)

            title_hint = page.title()
            for sep in ['|', '-', '—', '•']:
                if sep in title_hint:
                    title_hint = title_hint.split(sep)[0].strip()
                    break

            raw_sources = page.evaluate("""
                () => {
                    const urls = [];
                    const root = document.querySelector('main') || document.body;
                    root.querySelectorAll('img, picture source, source').forEach(el => {
                        const src = el.getAttribute('src') 
                            || el.getAttribute('data-src') 
                            || el.getAttribute('data-original') 
                            || el.getAttribute('srcset')
                            || el.getAttribute('data-srcset');
                        if (src) urls.push(src);
                    });
                    return urls;
                }
            """)

            filtered_sources = []
            for raw in raw_sources:
                target = raw

                if ',' in target:
                    target = target.split(',')[-1].strip().split(' ')[0]
                elif ' ' in target:
                    target = target.strip().split(' ')[0]

                if target.startswith('//'):
                    target = f"https:{target}"

                target_lower = target.lower()
                has_format = any(ext in target_lower for ext in valid_extensions)
                is_cdn = any(term in target_lower for term in [
                    '/image', '/foto', '/product', 'cdn', 'media', 
                    'static', 'ztat.net', 'uniqlo.com'
                ])
                is_ignored = any(kw in target_lower for kw in ignored_keywords)

                if (has_format or is_cdn) and not is_ignored and target.startswith('http'):
                    filtered_sources.append(target)

            candidates = clean_and_deduplicate_urls(filtered_sources)

        finally:
            browser.close()

    if not candidates:
        raise ValueError("No se encontraron imágenes en el producto facilitado.")

    return {
        "title_hint": title_hint,
        "images": candidates[:15]
    }