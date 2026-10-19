import os
import re
import uuid
import unicodedata
from PIL import Image
from flask import current_app


def slugify(value: str) -> str:
    """Converte um título em um slug amigável para URL."""
    value = str(value or "")
    value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


def save_image_as_webp(file_storage, prefix="img", max_width=1280) -> str | None:
    """Salva um upload de imagem convertendo automaticamente para WebP otimizado."""
    if not file_storage or not file_storage.filename:
        return None

    try:
        upload_dir = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_dir, exist_ok=True)

        img = Image.open(file_storage.stream)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int(float(img.height) * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        filename = f"{prefix}_{uuid.uuid4().hex[:12]}.webp"
        filepath = os.path.join(upload_dir, filename)
        img.save(filepath, "WEBP", quality=85, method=6)
        return f"/static/uploads/{filename}"
    except Exception as exc:
        current_app.logger.error(f"Erro ao converter imagem para WebP: {exc}")
        return None
