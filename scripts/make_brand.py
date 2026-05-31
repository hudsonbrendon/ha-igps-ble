"""Gera os ícones/logos do brand do HA a partir do logo oficial iGPSPORT.

Especificação HA brands:
- icon: quadrado, 256x256 (icon.png) e 512x512 (icon@2x.png).
- logo: largura até 512 (logo.png) / 1024 (logo@2x.png), altura proporcional.
- variantes dark_*: mesmas dimensões, para temas escuros.

Uso: python scripts/make_brand.py assets/igpsport-logo.png custom_components/igps/brand
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


def _square(img: Image.Image, size: int) -> Image.Image:
    """Encaixa o logo num canvas quadrado transparente, centralizado."""
    src = img.copy()
    src.thumbnail((size, size), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(src, ((size - src.width) // 2, (size - src.height) // 2), src)
    return canvas


def _wide(img: Image.Image, width: int) -> Image.Image:
    """Redimensiona mantendo proporção para a largura alvo."""
    ratio = width / img.width
    return img.resize((width, max(1, round(img.height * ratio))), Image.LANCZOS)


def _dark_variant(img: Image.Image) -> Image.Image:
    """Versão para fundo escuro: inverte luminância preservando alpha.

    Para logos coloridos, troque esta função por uma arte clara dedicada.
    """
    r, g, b, a = img.split()
    rgb = Image.merge("RGB", (r, g, b))
    from PIL import ImageOps

    inverted = ImageOps.invert(rgb)
    ir, ig, ib = inverted.split()
    return Image.merge("RGBA", (ir, ig, ib, a))


def main(src_path: str, out_dir: str) -> None:
    src = Image.open(src_path).convert("RGBA")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    _square(src, 256).save(out / "icon.png")
    _square(src, 512).save(out / "icon@2x.png")
    _wide(src, 512).save(out / "logo.png")
    _wide(src, 1024).save(out / "logo@2x.png")

    dark = _dark_variant(src)
    _square(dark, 256).save(out / "dark_icon.png")
    _square(dark, 512).save(out / "dark_icon@2x.png")
    _wide(dark, 512).save(out / "dark_logo.png")
    _wide(dark, 1024).save(out / "dark_logo@2x.png")

    print(f"Gerado em {out}:")
    for f in sorted(out.glob("*.png")):
        print(" -", f.name, Image.open(f).size)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("uso: python scripts/make_brand.py <logo.png> <out_dir>")
    main(sys.argv[1], sys.argv[2])
