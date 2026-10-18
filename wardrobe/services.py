import io
from PIL import Image
from rembg import remove
from django.core.files.base import ContentFile

def remove_background_and_crop(image_field) -> ContentFile:

    # 1. Leemos los bytes del archivo original
    image_field.seek(0)
    input_bytes = image_field.read()

    # 2. rembg elimina el fondo devolviendo bytes con canal alfa (RGBA)
    output_bytes = remove(input_bytes)

    # 3. Abrimos el resultado con Pillow para recortar márgenes vacíos
    image = Image.open(io.BytesIO(output_bytes))
    image = image.convert("RGBA")

    # getbbox() calcula la caja que encierra los píxeles visibles (no transparentes)
    bounding_box = image.getbbox()
    if bounding_box:
        image = image.crop(bounding_box)

    # 4. Guardamos la imagen en memoria en formato PNG para mantener la transparencia
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)

    # 5. Generamos el archivo de Django a partir del buffer
    filename = f"processed_{image_field.name.split('/')[-1].split('.')[0]}.png"
    return ContentFile(buffer.getvalue(), name=filename)