import io
from PIL import Image
from rembg import remove
from django.core.files.base import ContentFile

def remove_background_and_crop(image_field) -> ContentFile:
    if hasattr(image_field, 'open'):
        image_field.open()

    image_field.seek(0)
    input_bytes = image_field.read()

    if not input_bytes:
        return None

    # 1. Eliminación de fondo con rembg directamente sobre los bytes originales
    output_bytes = remove(input_bytes)

    # 2. Apertura en Pillow para recortar espacios transparentes
    image = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
    bounding_box = image.getbbox()
    if bounding_box:
        image = image.crop(bounding_box)

    # 3. Guardado final en PNG transparente
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)

    original_name = image_field.name.split('/')[-1].split('.')[0]
    filename = f"processed_{original_name}.png"
    return ContentFile(buffer.getvalue(), name=filename)