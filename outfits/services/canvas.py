import io
import logging
from typing import Dict, List, Optional, Tuple
from PIL import Image
from django.core.files.base import ContentFile
from wardrobe.models import ClothingItem

logger = logging.getLogger(__name__)


class OutfitCanvasGenerator:
    """
    Genera un lienzo visual (canvas) combinando las prendas recortadas (processed_image)
    de un Outfit respetando slots proporcionales según la categoría de cada prenda.
    Separa con suficiente holgura horizontal las prendas del torso y las alinea por la parte superior.
    """

    CANVAS_WIDTH: int = 1080
    CANVAS_HEIGHT: int = 1350
    BG_COLOR: Tuple[int, int, int, int] = (248, 249, 250, 255)  # #F8F9FA en RGBA

    CATEGORY_SLOTS: Dict[str, dict] = {
        'TOP': {
            'box': (0.12, 0.10, 0.46, 0.40),
            'z_index': 10,
        },
        'DRESS': {
            'box': (0.12, 0.10, 0.46, 0.65),
            'z_index': 10,
        },
        'OUTERWEAR': {
            'box': (0.08, 0.08, 0.54, 0.44),
            'z_index': 20,
        },
        'BOTTOM': {
            'box': (0.12, 0.48, 0.46, 0.32),
            'z_index': 10,
        },
        'SHOES': {
            'box': (0.18, 0.80, 0.34, 0.15),
            'z_index': 10,
        },
        'ACCESSORY': {
            'box': (0.65, 0.10, 0.27, 0.30),
            'z_index': 10,
        },
    }

    DEFAULT_SLOT: dict = {
        'box': (0.65, 0.48, 0.27, 0.30),
        'z_index': 5,
    }

    def __init__(self, clothes: List[ClothingItem]):
        self.clothes = clothes

    def generate(self) -> Optional[ContentFile]:
        canvas = Image.new('RGBA', (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), self.BG_COLOR)

        sorted_clothes = sorted(
            self.clothes,
            key=lambda item: self._get_slot_config(item.category).get('z_index', 0)
        )

        torso_items = [item for item in sorted_clothes if item.category in ('TOP', 'DRESS')]
        has_torso_collision = len(torso_items) >= 2
        torso_index = 0

        rendered_count = 0

        for item in sorted_clothes:
            image_field = item.processed_image or item.image
            if not image_field:
                continue

            try:
                with image_field.open('rb') as img_file:
                    item_img = Image.open(img_file).convert('RGBA')

                item_img = self._trim_transparent_borders(item_img)

                slot = self._get_slot_config(item.category)
                bx, by, bw, bh = slot['box']

                # Desplazamiento horizontal con holgura si hay más de una prenda en el torso
                if has_torso_collision and item.category in ('TOP', 'DRESS'):
                    bw = bw * 0.76
                    if torso_index == 0:
                        bx = 0.05
                    else:
                        bx = 0.48
                    torso_index += 1

                target_w = int(bw * self.CANVAS_WIDTH)
                target_h = int(bh * self.CANVAS_HEIGHT)

                resized_img = self._resize_contained(item_img, target_w, target_h)

                paste_x = int(bx * self.CANVAS_WIDTH) + (target_w - resized_img.width) // 2

                # Alineación superior para hombros y cuellos
                if item.category in ('TOP', 'DRESS', 'OUTERWEAR'):
                    paste_y = int(by * self.CANVAS_HEIGHT)
                else:
                    paste_y = int(by * self.CANVAS_HEIGHT) + (target_h - resized_img.height) // 2

                canvas.paste(resized_img, (paste_x, paste_y), mask=resized_img.split()[3])
                rendered_count += 1

            except Exception as e:
                logger.error("Error al procesar la prenda ID %s para el canvas: %s", item.id, e)
                continue

        if rendered_count == 0:
            return None

        final_image = Image.new('RGB', canvas.size, self.BG_COLOR[:3])
        final_image.paste(canvas, mask=canvas.split()[3])

        buffer = io.BytesIO()
        final_image.save(buffer, format='JPEG', quality=90, optimize=True)
        buffer.seek(0)

        return ContentFile(buffer.getvalue(), name="canvas.jpg")

    def _get_slot_config(self, category: str) -> dict:
        return self.CATEGORY_SLOTS.get(category.upper(), self.DEFAULT_SLOT)

    @staticmethod
    def _trim_transparent_borders(img: Image.Image) -> Image.Image:
        bbox = img.getbbox()
        return img.crop(bbox) if bbox else img

    @staticmethod
    def _resize_contained(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
        img_copy = img.copy()
        img_copy.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        return img_copy